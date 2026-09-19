"""FSG1f opt-in single-update, footprint-supported reciprocity candidate.

RGB/calibration/instance IDs ONLY. No evaluator import, truth access, parameter
search, or default change. Controls are predefined ablations, not alternatives
selected after evaluation. Consistent wrong surfaces can still pass this filter.
"""
from __future__ import annotations
import ast
import inspect
import json
from pathlib import Path
import time
import numpy as np
import cv2
import fsg_stereo as legacy
import fsg_stereo_hdr as hdr
from fsg_stereo import (BLOCK_SIZE, LR_TOLERANCE_PX, UNIQUENESS_RATIO,
    INSTANCE_GUARD_PX, MIN_LOCAL_STD_U8, rectification, remap, support_mask,
    mask_interior, matcher, pixels, reproject_q, rect_to_head)
from fsg_stereo_hdr import hdr_to_u8

CANDIDATE_ID = 'FSG1f-one-update-supported-reciprocity-v1'
VARIANTS = ('one_step_control', 'endpoint_control', 'candidate')
VARIANT_NOTES = {
    'one_step_control': 'One identical original photometric update; old interpolated LR acceptance recomputed.',
    'endpoint_control': 'One update plus all strictly positive-weight endpoint disparity agreements.',
    'candidate': 'One update plus endpoint agreement and a full 5x5 reciprocal footprint in both images.'}

def refine_once(left: np.ndarray, right: np.ndarray, initial: np.ndarray,
                     supported: np.ndarray) -> np.ndarray:
    """Bounded local photometric alignment after the discrete SGBM search.

    One original Gauss-Newton update, <=0.5 px; legacy total cap stays 0.75 px. Uses float
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
    for _ in range(1):
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


def compute_once(c: dict,obs: dict) -> tuple[dict,dict]:
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
    dl=refine_once(colours["L"],colours["R"],dl,vl&support["L"])
    dr=refine_once(colours["R"],colours["L"],dr,vr&support["R"])
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
              "matcher":{"name":"SGBM_3WAY+bounded_photometric_refinement","refinement_iterations":1,"maximum_refinement_px":0.75,"block_size":BLOCK_SIZE,"uniqueness_ratio":UNIQUENESS_RATIO,
                         "lr_tolerance_px":LR_TOLERANCE_PX,"min_disparity":minimum,"num_disparities":nd,
                         "instance_guard_px":INSTANCE_GUARD_PX,"minimum_local_std_u8":MIN_LOCAL_STD_U8},
              "depth_bounds_z_rect_m":[lo,hi],"crop_xywh":r["crop_xywh"].tolist(),
              "rectified_focal_px":float(r["P1"][0,0]),
              "quality_note":"LR residual and texture are diagnostics, not calibrated uncertainty",
              "point_frame":c["map_frame"]}
    state=dict(disparity_left=dl,disparity_right=dr,valid_left=vl,valid_right=vr,
               support_left=support["L"],support_right=support["R"],
               ids_left=ids["L"],ids_right=ids["R"])
    return record,metadata,state


# refine_once changes only the iteration count and its explanatory docstring.
# Its reachable per-step bound is 0.5 px; the unchanged
# original total cap of 0.75 px cannot be reached from the initial state in one step.

def check_kernel_equivalence() -> None:
    """Fail if the first-step arithmetic or other stereo settings drift."""
    hdr.check_kernel_equivalence()
    expected=inspect.getsource(legacy.refine_disparity).replace(
        'def refine_disparity(', 'def refine_once(').replace('range(3)', 'range(1)').replace(
        'Three Gauss-Newton updates, each <=0.5 px and total <=0.75 px.',
        'One original Gauss-Newton update, <=0.5 px; legacy total cap stays 0.75 px.')
    if ast.dump(ast.parse(expected)) != ast.dump(ast.parse(inspect.getsource(refine_once))):
        raise ValueError('single-step refiner differs beyond range(3) -> range(1)')
    expected=inspect.getsource(hdr.compute_hdr).replace('def compute_hdr(', 'def compute_once(').replace(
        'refine_disparity(', 'refine_once(').replace('"refinement_iterations":3', '"refinement_iterations":1')
    capture = '    state=dict(disparity_left=dl,disparity_right=dr,valid_left=vl,valid_right=vr,\n' \
              '               support_left=support["L"],support_right=support["R"],\n' \
              '               ids_left=ids["L"],ids_right=ids["R"])\n'
    expected=expected.replace('    return record,metadata',capture+'    return record,metadata,state')
    if ast.dump(ast.parse(expected)) != ast.dump(ast.parse(inspect.getsource(compute_once))):
        raise ValueError('single-step kernel changed beyond iteration count and diagnostic capture')


def endpoint_cycle(source_d: np.ndarray, target_d: np.ndarray,
                   source_good: np.ndarray, target_good: np.ndarray,
                   source_ids: np.ndarray, target_ids: np.ndarray) -> dict:
    """Require disparity reciprocity at EVERY nonzero bilinear contributor.

    Rectified correspondences share integer row coordinates. At x = u - d(u),
    test d_source(u) + d_target(floor(x)) and ...ceil(x) separately, not their
    weighted average. A contributor of exactly zero weight is NOT tested.
    This is a consistency filter, not a visibility certificate. No quantization
    of the coordinate is used to hide a small positive contribution.
    """
    shape=source_d.shape
    if len(shape)!=2 or any(a.shape!=shape for a in
            (target_d,source_good,target_good,source_ids,target_ids)):
        raise ValueError('cycle arrays must share a 2D shape')
    height,width=shape;vv,uu=np.indices(shape)
    finite=np.isfinite(source_d);x=uu-source_d.astype(np.float64)
    safe_x=np.where(finite,x,0.)
    within=finite&(x>=0)&(x<=width-1)
    # Clip before integer conversion to remain safe even for invalid huge values.
    bounded=np.clip(safe_x,-1,width)
    x0=np.floor(bounded).astype(np.int64);x1=x0+1
    w1=bounded-x0;active0=(1.-w1)>0.;active1=w1>0.
    ok=source_good.astype(bool)&within&(source_ids>0)
    maximum=np.zeros(shape,np.float64)
    supported=np.ones(shape,bool);same_ids=np.ones(shape,bool)
    for ix,active in ((x0,active0),(x1,active1)):
        inside=(ix>=0)&(ix<width);ixsafe=np.clip(ix,0,width-1)
        other=target_d[vv,ixsafe]
        res=np.abs(source_d.astype(np.float64)+other.astype(np.float64))
        good=inside&target_good[vv,ixsafe]&np.isfinite(other)
        same=target_ids[vv,ixsafe]==source_ids
        supported &= ~active|good
        same_ids &= ~active|same
        ok &= ~active|(good&same&(res<=LR_TOLERANCE_PX))
        maximum=np.maximum(maximum,np.where(active,res,0.))
    return dict(ok=ok,coordinate=x,x0=x0,x1=x1,weight1=w1,
                active0=active0,active1=active1,max_active_residual=maximum,
                all_active_supported=supported&within,all_active_same_id=same_ids)


def footprint_support(mask: np.ndarray) -> np.ndarray:
    """Every reciprocal test in the existing BLOCK_SIZE x BLOCK_SIZE footprint.

    This deliberately costs coverage near missing support and thin structures.
    It does not require neighbouring disparities to be equal: each neighbour
    has its own estimated correspondence and reciprocal test.
    """
    return cv2.erode(mask.astype(np.uint8),np.ones((BLOCK_SIZE,BLOCK_SIZE),np.uint8),
                     borderType=cv2.BORDER_CONSTANT,borderValue=0).astype(bool)


def sample_all_active(mask: np.ndarray, endpoints: dict) -> np.ndarray:
    height,width=mask.shape;vv=np.indices(mask.shape)[0]
    good=np.isfinite(endpoints['coordinate'])&(endpoints['coordinate']>=0)&(endpoints['coordinate']<=width-1)
    for key,active_key in (('x0','active0'),('x1','active1')):
        ix=endpoints[key];active=endpoints[active_key]
        inside=(ix>=0)&(ix<width)
        good &= ~active|(inside&mask[vv,np.clip(ix,0,width-1)])
    return good


def supported_cycles(state: dict) -> dict:
    gl=state['valid_left']&state['support_left'];gr=state['valid_right']&state['support_right']
    l=endpoint_cycle(state['disparity_left'],state['disparity_right'],gl,gr,
                     state['ids_left'],state['ids_right'])
    r=endpoint_cycle(state['disparity_right'],state['disparity_left'],gr,gl,
                     state['ids_right'],state['ids_left'])
    lp=footprint_support(l['ok']);rp=footprint_support(r['ok'])
    right_footprint=sample_all_active(rp,l)
    return dict(endpoint_left=l['ok'],endpoint_right=r['ok'],footprint_left=lp,
                footprint_right=rp,right_footprint_at_match=right_footprint,
                supported_cycle=l['ok']&lp&right_footprint,
                max_active_endpoint_residual=l['max_active_residual'],
                endpoint_weight1=l['weight1'],all_active_supported=l['all_active_supported'],
                all_active_same_id=l['all_active_same_id'])


def subset_record(record: dict, valid: np.ndarray) -> dict:
    if valid.shape!=record['valid'].shape or np.any(valid&~record['valid']):
        raise ValueError('candidate may only subset its freshly recomputed one-step support')
    result={key:value.copy() for key,value in record.items()}
    result['valid']=valid.copy()
    for key in ('xyz_h','range_left_m','z_rect_m'):
        result[key][~valid]=np.nan
    return result


def compute_variants(c: dict, obs: dict) -> tuple[dict,dict,dict]:
    """One frozen candidate and two predeclared ablation controls. No truth."""
    start=time.perf_counter();check_kernel_equivalence()
    one,meta,state=compute_once(c,obs)
    checks=supported_cycles(state)
    x,y,width,height=map(int,one['crop_xywh']);sl=np.s_[y:y+height,x:x+width]
    endpoint=one['valid']&checks['endpoint_left'][sl]
    final=one['valid']&checks['supported_cycle'][sl]
    records={'one_step_control':one,'endpoint_control':subset_record(one,endpoint),
             'candidate':subset_record(one,final)}
    fields={key:value[sl].copy() for key,value in checks.items()}
    fields.update(one_step_valid=one['valid'].copy(),endpoint_control_valid=endpoint.copy(),
                  candidate_valid=final.copy(),refinement_shift_px=one['disparity_px']-one['disparity_sgbm_px'])
    metadata={}
    for name,result in records.items():
        item=json.loads(json.dumps(meta));item['schema']='FSG1f-stereo-v1'
        item.update(candidate_id=CANDIDATE_ID,variant=name,variant_note=VARIANT_NOTES[name],
                    encoding=dict(hdr.ENCODING),adopted_default=False,
                    valid_count=int(result['valid'].sum()),valid_fraction_core=float(result['valid'].mean()),
                    inference_seconds_shared=time.perf_counter()-start,
                    selection_on_diagnostic_records=True,
                    visibility_is_certified=False)
        item['matcher'].update(name='SGBM_3WAY+one_original_photometric_update',
                               refinement_iterations=1,reachable_maximum_refinement_px=0.5,
                               endpoint_tolerance_px=LR_TOLERANCE_PX,
                               reciprocal_footprint_size=BLOCK_SIZE)
        item['quality_note']='Neither cycle agreement nor neighbourhood support is calibrated visibility or uncertainty.'
        metadata[name]=item
    return records,metadata,fields


def reconstruct_pair(folder: Path, out: Path) -> dict:
    """Inference-only entrypoint; output must lie outside the immutable input."""
    folder,out=folder.resolve(),out.resolve()
    if out.is_relative_to(folder) or folder.is_relative_to(out) or out.exists():
        raise ValueError('output must be NEW and separate from the source observation')
    c,obs=hdr.read_observation(folder);records,meta,fields=compute_variants(c,obs)
    fingerprints={name:legacy.sha256(folder/name) for name in ('calibration.json','observation.npz')}
    for name in VARIANTS:
        meta[name]['input_sha256']=fingerprints
        hdr.save_candidate(out/name,c,records[name],meta[name])
    np.savez_compressed(out/'rgb_acceptance_trace.npz',**fields)
    return {name:meta[name]['valid_count'] for name in VARIANTS}


if __name__=='__main__':
    import argparse,sys
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('pair',type=Path)
    ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    try:
        result=reconstruct_pair(args.pair,args.out)
        print('[fsg-supported] COMPLETE',json.dumps(result),'new_primary_samples=0')
    except Exception as exc:
        print(f'[fsg-supported] FAIL {type(exc).__name__}: {exc}',file=sys.stderr);raise SystemExit(1)
