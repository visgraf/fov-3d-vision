"""FSG1c fixed HDR encoding candidate. RGB inference only; never reads truth.

The copied compute body differs from frozen fsg_stereo.compute ONLY in its name
and the RGB-to-uint8 function. check_kernel_equivalence enforces that invariant.
This keeps legacy files byte-identical and avoids mutating module globals.
The new encoding is an experimental instrument, NOT an adopted default.
"""
from __future__ import annotations
import ast
import inspect
import json
from pathlib import Path
import time
import numpy as np
import cv2
from PIL import Image
import fsg_stereo as legacy
from fsg_stereo import (BLOCK_SIZE, LR_TOLERANCE_PX, UNIQUENESS_RATIO,
    INSTANCE_GUARD_PX, MIN_LOCAL_STD_U8, rectification, remap, support_mask,
    mask_interior, matcher, refine_disparity, pixels, reproject_q, rect_to_head)
from fsg_geometry import json_write

CANDIDATE_ID = 'FSG1c-fixed-soft-hdr-srgb-v1'
ENCODING = {'id': CANDIDATE_ID, 'formula': 'sRGB(max(x,0)/(1+max(x,0))) then round(255*y)',
            'fixed_scale_scene_linear_units': 1.0, 'same_for_both_eyes': True,
            'per_eye_normalization': False, 'refinement_input': 'original scene-linear RGB',
            'texture_input': 'same encoded uint8 grayscale supplied to SGBM',
            'warning': 'Quantization remains; positive gradients can be noise, not correspondence evidence.'}


def hdr_to_u8(rgb: np.ndarray) -> np.ndarray:
    """Fixed pointwise mapping. No fitted exposure, statistics, IDs or truth.

    No finite positive input is hard-clipped at scene-linear 1.0. Very large
    values can still quantize to 255. Negative values retain the legacy floor.
    """
    a = np.asarray(rgb, dtype=np.float64)
    if not np.isfinite(a).all():
        raise ValueError('HDR encoding requires finite RGB')
    a = np.maximum(a, 0.)
    return legacy.linear_to_u8(a / (1. + a))


def check_kernel_equivalence() -> None:
    """A fail-capable guard against any hidden matcher/gate/refiner change."""
    expected = inspect.getsource(legacy.compute)
    if expected.count('linear_to_u8(') != 1:
        raise ValueError('unexpected legacy encoding call count')
    expected = expected.replace('def compute(', 'def compute_hdr(').replace('linear_to_u8(', 'hdr_to_u8(')
    actual = inspect.getsource(compute_hdr)
    if ast.dump(ast.parse(expected)) != ast.dump(ast.parse(actual)):
        raise ValueError('candidate kernel changed beyond the one encoding substitution')


def compute_hdr(c: dict,obs: dict) -> tuple[dict,dict]:
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
        gray[side]=cv2.cvtColor(hdr_to_u8(colours[side]),cv2.COLOR_RGB2GRAY)
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



def compute_candidate(c: dict, obs: dict) -> tuple[dict, dict]:
    check_kernel_equivalence()
    result, meta = compute_hdr(c, obs)
    meta['schema'] = 'FSG1c-stereo-candidate-v1'
    meta['candidate_id'] = CANDIDATE_ID
    meta['encoding'] = dict(ENCODING)
    meta['adopted_default'] = False
    return result, meta


def read_observation(folder: Path) -> tuple[dict, dict]:
    c = json.loads((folder / 'calibration.json').read_text())
    with np.load(folder / 'observation.npz', allow_pickle=False) as f:
        obs = {k: f[k] for k in f.files}
    return c, obs


def save_candidate(out: Path, c: dict, result: dict, meta: dict) -> None:
    """Write candidate artifacts only in a NEW directory, never legacy stereo/."""
    if out.exists():
        raise FileExistsError(f'candidate output exists: {out}')
    out.mkdir(parents=True)
    np.savez_compressed(out / 'result.npz', **result)
    json_write(out / 'summary.json', meta)
    for side, key in (('L', 'rgb_left'), ('R', 'rgb_right')):
        Image.fromarray(hdr_to_u8(result[key])).save(out / f'rectified_{side}_candidate.png')
        Image.fromarray(legacy.linear_to_u8(result[key])).save(out / f'rectified_{side}_legacy_display.png')
    m = result['valid']
    Image.fromarray(m.astype(np.uint8) * 255).save(out / 'validity.png')
    legacy.save_gray(out / 'disparity.png', result['disparity_px'], m, 0, float(result['num_disparities']))
    lo, hi = c['depth_search_z_rect_m']
    legacy.save_gray(out / 'range_left.png', result['range_left_m'], m, lo, hi)
    legacy.write_ply(out / 'candidate_points_head.ply', result['xyz_h'][m],
                     hdr_to_u8(result['rgb_left'])[m], result['instance_id'][m])


def reconstruct_pair(folder: Path, out: Path) -> tuple[dict, dict]:
    folder, out = folder.resolve(), out.resolve()
    if out.is_relative_to(folder) or folder.is_relative_to(out):
        raise ValueError('candidate output must be separate from source record')
    if out.exists():
        raise FileExistsError(f'candidate output exists: {out}')
    c, obs = read_observation(folder)
    result, meta = compute_candidate(c, obs)
    meta['input_sha256'] = {name: legacy.sha256(folder / name)
                            for name in ('calibration.json', 'observation.npz')}
    save_candidate(out, c, result, meta)
    return result, meta
