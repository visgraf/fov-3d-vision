"""FSG1 host-side local rectification, SGBM, and head-frame reconstruction.

    .venv/bin/python tools/fsg_stereo.py previews/fsg1/small

Reads calibration.json and observation.npz ONLY for inference. Never opens
'evaluation_only'. Full padded rasters are matched before the core is cropped.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import cv2
from PIL import Image

from fsg_geometry import (crop_q, json_write, pixels, relative_pose, reproject_q,
                          rect_to_head, validate_calibration)

BLOCK_SIZE = 5
LR_TOLERANCE_PX = 1.0
UNIQUENESS_RATIO = 10
INSTANCE_GUARD_PX = 3
MIN_LOCAL_STD_U8 = 0.5


def linear_to_u8(rgb: np.ndarray) -> np.ndarray:
    """One fixed transform, no per-eye exposure/contrast normalisation."""
    a = np.clip(np.asarray(rgb,float),0.,1.)
    a = np.where(a<=.0031308,12.92*a,1.055*np.power(a,1/2.4)-.055)
    return np.rint(255*a).astype(np.uint8)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rectification(c: dict) -> dict:
    validate_calibration(c)
    w,h = c["image_size_wh"]
    kl,kr = (np.asarray(e["K"],float) for e in c["eyes"])
    r,t = relative_pose(c)
    r1,r2,p1,p2,q,roi1,roi2 = cv2.stereoRectify(
        kl,np.zeros(5),kr,np.zeros(5),(w,h),r,t,
        flags=cv2.CALIB_ZERO_DISPARITY,alpha=-1,newImageSize=(w,h))
    if abs(p2[1,3])>1e-7 or p2[0,3]>=0:
        raise ValueError("expected horizontal rectification with positive L-R disparity")
    m = {}
    for side,k,rr,pp in (("L",kl,r1,p1),("R",kr,r2,p2)):
        mx,my = cv2.initUndistortRectifyMap(k,np.zeros(5),rr,pp[:,:3],(w,h),cv2.CV_32FC1)
        m["map_"+side+"x"] = mx; m["map_"+side+"y"] = my
    core = c["core_size"]; x=(w-core)//2; y=(h-core)//2
    q_core = crop_q(q,(x,y),(x,y))
    # Near search bound is fixed in rectified axial metres, not taken from truth.
    z_min,_ = c["depth_search_z_rect_m"]
    max_d = int(np.ceil(abs(p2[0,3])/z_min))+4
    n_disp = int(np.ceil(max_d/16)*16)
    if n_disp+2*BLOCK_SIZE >= w:
        raise ValueError("raw raster too narrow for declared disparity search")
    return dict(m,R1=r1,R2=r2,P1=p1,P2=p2,Q_full=q,Q_core=q_core,
                crop_xywh=np.array([x,y,core,core],np.int32),
                roi_L=np.array(roi1),roi_R=np.array(roi2),
                min_disparity=np.array(0),num_disparities=np.array(n_disp))


def remap(a: np.ndarray, r: dict, side: str, method: int) -> np.ndarray:
    return cv2.remap(a,r["map_"+side+"x"],r["map_"+side+"y"],method,
                     borderMode=cv2.BORDER_CONSTANT,borderValue=0)


def support_mask(c: dict,r: dict,side: str) -> np.ndarray:
    w,h = c["image_size_wh"]
    x,y = r["map_"+side+"x"],r["map_"+side+"y"]
    a = (x>=1)&(x<w-2)&(y>=1)&(y<h-2)
    return cv2.erode(a.astype(np.uint8),np.ones((BLOCK_SIZE,BLOCK_SIZE),np.uint8)).astype(bool)


def mask_interior(ids: np.ndarray,radius: int) -> np.ndarray:
    k = np.ones((2*radius+1,2*radius+1),np.uint8)
    a = ids.astype(np.float32)
    return (ids>0)&(cv2.erode(a,k)==a)&(cv2.dilate(a,k)==a)


def matcher(min_d: int, n: int):
    return cv2.StereoSGBM_create(minDisparity=min_d,numDisparities=n,blockSize=BLOCK_SIZE,
        P1=8*BLOCK_SIZE**2,P2=32*BLOCK_SIZE**2,disp12MaxDiff=-1,preFilterCap=31,
        uniquenessRatio=UNIQUENESS_RATIO,speckleWindowSize=0,speckleRange=1,
        mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY)


def refine_disparity(left: np.ndarray, right: np.ndarray, initial: np.ndarray,
                     supported: np.ndarray) -> np.ndarray:
    """Bounded local photometric alignment after the discrete SGBM search.

    Three Gauss-Newton updates, each <=0.5 px and total <=0.75 px. Uses float
    luminance, not truth, labels, or a fitted depth correction. Removing the local
    residual mean admits a small additive brightness difference. This refines a
    chosen peak; it cannot solve an incorrect correspondence or an occlusion.
    """
    l = np.asarray(left, np.float32) @ np.array([.2126,.7152,.0722],np.float32)
    r = np.asarray(right, np.float32) @ np.array([.2126,.7152,.0722],np.float32)
    grad = cv2.Sobel(r,cv2.CV_32F,1,0,ksize=3,scale=1/8)
    h,w=l.shape; vv,uu=np.mgrid[:h,:w].astype(np.float32)
    d=initial.copy()
    mean=lambda a: cv2.boxFilter(a,-1,(5,5),normalize=True,borderType=cv2.BORDER_REFLECT)
    for _ in range(3):
        x=uu-d
        rw=cv2.remap(r,x,vv,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        gw=cv2.remap(grad,x,vv,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        residual=rw-l
        gm=mean(gw); rm=mean(residual)
        numerator=mean(gw*residual)-gm*rm
        denominator=np.maximum(mean(gw*gw)-gm*gm,0.)
        step=np.divide(numerator,denominator+1e-9,out=np.zeros_like(d),where=denominator>1e-8)
        update=np.clip(step,-.5,.5)
        d=np.where(supported,np.clip(d+update,initial-.75,initial+.75),initial).astype(np.float32)
    return d


def compute(c: dict,obs: dict) -> tuple[dict,dict]:
    t0=time.perf_counter()
    expected={"rgb_L","rgb_R","instance_L","instance_R"}
    if set(obs)!=expected:
        raise ValueError(f"observation must contain exactly {sorted(expected)}, not geometry")
    w,h=c["image_size_wh"]
    for side in ("L","R"):
        if obs["rgb_"+side].shape!=(h,w,3) or not np.isfinite(obs["rgb_"+side]).all():
            raise ValueError("RGB dimensions or finite-value check failed")
        ids=obs["instance_"+side]
        if ids.shape!=(h,w) or ids.dtype.kind not in "iu" or np.any(ids<0):
            raise ValueError("oracle instance mask must be nonnegative integer IDs")
    r=rectification(c)
    gray={}; colours={}; ids={}; support={}
    for side in ("L","R"):
        colours[side]=remap(obs["rgb_"+side],r,side,cv2.INTER_LINEAR)
        gray[side]=cv2.cvtColor(linear_to_u8(colours[side]),cv2.COLOR_RGB2GRAY)
        ids[side]=remap(obs["instance_"+side].astype(np.float32),r,side,cv2.INTER_NEAREST).astype(np.int32)
        support[side]=support_mask(c,r,side)&mask_interior(ids[side],INSTANCE_GUARD_PX)
    nd=int(r["num_disparities"]); minimum=int(r["min_disparity"])
    # OpenCV returns 1/16-pixel fixed point; invalid value is (minDisparity-1)*16.
    dl_raw=matcher(minimum,nd).compute(gray["L"],gray["R"])
    min_right=-(minimum+nd-1)
    dr_raw=matcher(min_right,nd).compute(gray["R"],gray["L"])
    dl=dl_raw.astype(np.float32)/16.; dr=dr_raw.astype(np.float32)/16.
    vl=dl_raw>(minimum-1)*16; vr=dr_raw>(min_right-1)*16
    dl_discrete=dl.copy()
    dl=refine_disparity(colours["L"],colours["R"],dl,vl&support["L"])
    dr=refine_disparity(colours["R"],colours["L"],dr,vr&support["R"])
    uv=pixels(w,h); ur=uv[...,0]-dl; v=uv[...,1].astype(np.float32)
    xr=ur.astype(np.float32)
    dr_at=cv2.remap(dr,xr,v,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    vr_at=cv2.remap((vr&support["R"]).astype(np.float32),xr,v,cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_CONSTANT,borderValue=0)>.999
    rid=cv2.remap(ids["R"].astype(np.float32),xr,v,cv2.INTER_NEAREST,
                 borderMode=cv2.BORDER_CONSTANT,borderValue=0).astype(np.int32)
    lr=np.abs(dl+dr_at)
    m=gray["L"].astype(np.float32)
    std=np.sqrt(np.maximum(cv2.boxFilter(m*m,-1,(5,5))-cv2.boxFilter(m,-1,(5,5))**2,0.))
    valid=vl&vr_at&support["L"]&(ur>=0)&(ur<w-1)&(lr<=LR_TOLERANCE_PX)&(rid==ids["L"])&(std>=MIN_LOCAL_STD_U8)
    rect_xyz=reproject_q(r["Q_full"],uv,dl)
    z=rect_xyz[...,2]
    lo,hi=c["depth_search_z_rect_m"]
    valid &= np.isfinite(rect_xyz).all(axis=-1)&(z>=lo)&(z<=hi)
    # Honor SGBM's own disparity support ROI rather than accepting padded borders.
    roi=cv2.getValidDisparityROI(tuple(r["roi_L"]),tuple(r["roi_R"]),minimum,nd,BLOCK_SIZE)
    gx,gy,gw,gh=roi; geometric_support=np.zeros((h,w),bool)
    geometric_support[gy:gy+gh,gx:gx+gw]=True
    valid &= geometric_support
    xyz_h=rect_to_head(c,r["R1"],np.where(np.isfinite(rect_xyz),rect_xyz,np.nan))
    eye_range=np.linalg.norm(xyz_h-np.asarray(c["eyes"][0]["centre_h_m"]),axis=-1)
    x,y,cw,ch=map(int,r["crop_xywh"]); sl=np.s_[y:y+ch,x:x+cw]
    point=xyz_h[sl].astype(np.float32); keep=valid[sl]
    point[~keep]=np.nan
    distance=np.where(keep,eye_range[sl],np.nan).astype(np.float32)
    record=dict(r, disparity_px=dl[sl], disparity_sgbm_px=dl_discrete[sl], disparity_right_full_px=dr,
                xyz_h=point,valid=keep,range_left_m=distance,
                z_rect_m=np.where(keep,z[sl],np.nan).astype(np.float32),
                lr_error_px=lr[sl],instance_id=ids["L"][sl],
                rgb_left=colours["L"][sl],rgb_right=colours["R"][sl],
                left_gray_std=std[sl],
                # Reference support is calibration-derived, NOT inferred coverage.
                raw_support_L=support_mask(c,r,"L")[sl])
    metadata={"schema":"FSG1-stereo-v1","valid_count":int(keep.sum()),"core_pixels":int(keep.size),
              "valid_fraction_core":float(keep.mean()),"seconds":time.perf_counter()-t0,
              "opencv":cv2.__version__,"numpy":np.__version__,
              "matcher":{"name":"SGBM_3WAY+bounded_photometric_refinement","refinement_iterations":3,"maximum_refinement_px":0.75,"block_size":BLOCK_SIZE,"uniqueness_ratio":UNIQUENESS_RATIO,
                         "lr_tolerance_px":LR_TOLERANCE_PX,"min_disparity":minimum,"num_disparities":nd,
                         "instance_guard_px":INSTANCE_GUARD_PX,"minimum_local_std_u8":MIN_LOCAL_STD_U8},
              "depth_bounds_z_rect_m":[lo,hi],"crop_xywh":r["crop_xywh"].tolist(),
              "rectified_focal_px":float(r["P1"][0,0]),
              "quality_note":"LR residual and texture are diagnostics, not calibrated uncertainty",
              "point_frame":c["map_frame"]}
    return record,metadata


def save_gray(path: Path,a: np.ndarray,valid: np.ndarray,lo: float,hi: float) -> None:
    a=np.nan_to_num(a,nan=lo,posinf=hi,neginf=lo)
    z=np.clip((a-lo)/max(hi-lo,1e-12),0.,1.)
    image=np.where(valid,np.rint(32+223*z),0).astype(np.uint8)
    Image.fromarray(image).save(path)


def write_ply(path: Path,xyz: np.ndarray,rgb: np.ndarray,ids: np.ndarray) -> None:
    with path.open("w") as f:
        f.write("ply\nformat ascii 1.0\ncomment fixed H: +X right +Y up -Z forward; metres\n")
        f.write(f"element vertex {len(xyz)}\nproperty float x\nproperty float y\nproperty float z\n")
        f.write("property uchar red\nproperty uchar green\nproperty uchar blue\nproperty int instance_id\nend_header\n")
        for p,col,i in zip(xyz,rgb,ids):
            f.write(f"{p[0]:.8g} {p[1]:.8g} {p[2]:.8g} {col[0]} {col[1]} {col[2]} {i}\n")


def process_pair(folder: Path,out: Path | None=None) -> dict:
    out=out or folder/"stereo"
    if out.exists() and any(out.iterdir()): raise FileExistsError(f"stereo output already exists: {out}")
    c=json.loads((folder/"calibration.json").read_text())
    with np.load(folder/"observation.npz",allow_pickle=False) as a:
        obs={k:a[k] for k in a.files}
    result,summary=compute(c,obs)
    summary["input_sha256"]={n:sha256(folder/n) for n in ("calibration.json","observation.npz")}
    out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/"result.npz",**result)
    for side,key in (("L","rgb_left"),("R","rgb_right")):
        Image.fromarray(linear_to_u8(result[key])).save(out/f"rectified_{side}.png")
    Image.fromarray(result["valid"].astype(np.uint8)*255).save(out/"validity.png")
    save_gray(out/"disparity.png",result["disparity_px"],result["valid"],0,float(result["num_disparities"]))
    lo,hi=c["depth_search_z_rect_m"]
    save_gray(out/"range_left.png",result["range_left_m"],result["valid"],lo,hi)
    m=result["valid"]
    write_ply(out/"points_head.ply",result["xyz_h"][m],linear_to_u8(result["rgb_left"])[m],result["instance_id"][m])
    json_write(out/"summary.json",summary)
    print(f"[fsg-stereo] {folder.name} valid={summary['valid_count']}/{summary['core_pixels']} "
          f"fraction={summary['valid_fraction_core']:.4f} ndisp={summary['matcher']['num_disparities']} seconds={summary['seconds']:.4f}")
    return summary


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument("run",type=Path)
    args=ap.parse_args()
    if (args.run/"calibration.json").is_file():
        process_pair(args.run)
    else:
        run=json.loads((args.run/"run.json").read_text())
        if not run.get("complete"): raise ValueError("acquisition is incomplete")
        for name in run["cases"]: process_pair(args.run/name)


if __name__=="__main__":
    try: main()
    except Exception as e:
        print(f"[fsg-stereo] FAIL {type(e).__name__}: {e}",file=sys.stderr)
        raise SystemExit(1)
