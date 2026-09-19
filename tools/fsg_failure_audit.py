"""FSG1e read-only stage/visibility audit. No new estimator or acceptance rule.

Replays seven FULL pairs (three seed-17 development, four FSG1d validation).
All diagnostic stage errors use the FROZEN final accepted support. Stage metrics
are NOT alternative instrument scores. No PLY or altered validity is exported.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import sys
import time
import numpy as np
import cv2
from PIL import Image, ImageDraw
import fsg_geometry as g
import fsg_stereo as s
import fsg_stereo_hdr as hdr
import fsg_coverage_audit as audit
import fsg_hdr_compare as paired
import fsg_validation_scene as spec
import fsg_validation_eval as validation
import fsg_evaluate as evaluate

AUDIT_ID = 'FSG1e-stage-visibility-audit-v1'
# Equality tolerance for detecting a float32 bound, NOT a quality threshold.
CAP_ATOL = 1e-6
EXTRA_FROZEN = {'fsg_validation_scene.py': 'a22b471b6d612273de4161604ec3364ed70e5933ce048c405f7ce3883a7eefa5', 'fsg_validation_eval.py': 'f9846309ea8fce93a2dbbcb487da7a98e75b000933e59eb198e0c917e936924c', 'fsg_validation_render.py': 'f18883e1e2764dd7a0e21e545fe9764698244802f9c8ff8188aa93fb73ba4cea'}
require = audit.require


def check_sources() -> dict:
    actual = spec.check_frozen()
    root = Path(__file__).resolve().parent
    extra = {n:s.sha256(root/n) for n in EXTRA_FROZEN}
    require(extra == EXTRA_FROZEN, 'FSG1d diagnostic/reference sources changed')
    hdr.check_kernel_equivalence()
    return dict(actual, **extra)


def trace_refinement(left: np.ndarray, right: np.ndarray, initial: np.ndarray,
                     supported: np.ndarray) -> dict:
    """Exact frozen arithmetic with instrumentation; independently replay-checked.

    No truth, paths, masks inferred from truth, or parameter choices enter here.
    The final equality check covers ALL pixels, not just accepted ones.
    """
    l=np.asarray(left,np.float32) @ np.array([.2126,.7152,.0722],np.float32)
    r=np.asarray(right,np.float32) @ np.array([.2126,.7152,.0722],np.float32)
    grad=cv2.Sobel(r,cv2.CV_32F,1,0,ksize=3,scale=1/8)
    h,w=l.shape;vv,uu=np.mgrid[:h,:w].astype(np.float32)
    d=initial.copy()
    mean=lambda a:cv2.boxFilter(a,-1,(5,5),normalize=True,borderType=cv2.BORDER_REFLECT)
    stages=[d.copy()]; numerators=[]; denominators=[]; steps=[]; costs=[]
    for _ in range(3):
        x=uu-d
        rw=cv2.remap(r,x,vv,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        gw=cv2.remap(grad,x,vv,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REFLECT)
        residual=rw-l
        gm=mean(gw);rm=mean(residual)
        numerator=mean(gw*residual)-gm*rm
        denominator=np.maximum(mean(gw*gw)-gm*gm,0.)
        step=np.divide(numerator,denominator+1e-9,out=np.zeros_like(d),where=denominator>1e-8)
        update=np.clip(step,-.5,.5)
        d=np.where(supported,np.clip(d+update,initial-.75,initial+.75),initial).astype(np.float32)
        numerators.append(numerator);denominators.append(denominator);steps.append(step)
        costs.append(np.maximum(mean(residual*residual)-rm*rm,0.))
        stages.append(d.copy())
    require(np.array_equal(d,s.refine_disparity(left,right,initial,supported),equal_nan=True),
            'instrumented refinement differs from frozen refinement')
    return {'stages':np.stack(stages),'numerator':np.stack(numerators),
            'denominator':np.stack(denominators),'unbounded_step':np.stack(steps),
            'residual_variance_before_update':np.stack(costs)}


def cap_masks(initial: np.ndarray, final: np.ndarray) -> dict:
    delta=final-initial
    lo=np.isclose(delta,-.75,rtol=0,atol=CAP_ATOL)
    hi=np.isclose(delta,.75,rtol=0,atol=CAP_ATOL)
    return {'lower_cap':lo,'upper_cap':hi,'not_at_cap':~(lo|hi)}


def cycle_endpoints(dl: np.ndarray, dr: np.ndarray, xr: np.ndarray, y: np.ndarray) -> dict:
    """Explain interpolation; endpoint agreement is diagnostic, not a new veto.

    OpenCV INTER_LINEAR uses its interpolation table; an ideal weighted sum is
    reported separately and is NOT asserted equal to the production remap.
    """
    h,w=dr.shape
    x0=np.floor(xr).astype(int);x1=x0+1;yy=y.astype(int)
    inside=(x0>=0)&(x1<w)&(yy>=0)&(yy<h)
    yy=np.clip(yy,0,h-1);x0c=np.clip(x0,0,w-1);x1c=np.clip(x1,0,w-1)
    signed0=dl+dr[yy,x0c];signed1=dl+dr[yy,x1c]
    mix=dl+cv2.remap(dr,xr.astype(np.float32),y.astype(np.float32),cv2.INTER_LINEAR,
                    borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    endpoint_pass=(np.abs(signed0)<=s.LR_TOLERANCE_PX)&(np.abs(signed1)<=s.LR_TOLERANCE_PX)
    return {'x0':x0,'x1':x1,'weight1_ideal':xr-x0,'inside':inside,
            'signed_residual_x0':signed0,'signed_residual_x1':signed1,
            'signed_residual_interpolated':mix,'both_endpoints_pass':inside&endpoint_pass,
            'interpolated_pass':inside&(np.abs(mix)<=s.LR_TOLERANCE_PX)}


def trace_rgb(c: dict, obs: dict, stored: dict, instrument: str) -> dict:
    """RGB-only exact replay plus traces. No filesystem/evaluator access."""
    require(instrument in ('legacy','hdr'), 'unknown instrument')
    fn=s.compute if instrument=='legacy' else hdr.compute_candidate
    fresh,_=fn(c,obs);audit.assert_replay(stored,fresh)
    r=s.rectification(c);w,h=c['image_size_wh']
    x,y,cw,ch=map(int,r['crop_xywh']);sl=np.s_[y:y+ch,x:x+cw]
    colors={};ids={};support={};gray={};raw={};valid_raw={};rt={}
    encoder=s.linear_to_u8 if instrument=='legacy' else hdr.hdr_to_u8
    minimum=int(r['min_disparity']);nd=int(r['num_disparities']);minimum_r=-(minimum+nd-1)
    for side in ('L','R'):
        colors[side]=s.remap(obs['rgb_'+side],r,side,cv2.INTER_LINEAR)
        ids[side]=s.remap(obs['instance_'+side].astype(np.float32),r,side,cv2.INTER_NEAREST).astype(np.int32)
        support[side]=s.support_mask(c,r,side)&s.mask_interior(ids[side],s.INSTANCE_GUARD_PX)
        gray[side]=cv2.cvtColor(encoder(colors[side]),cv2.COLOR_RGB2GRAY)
    for side,other,md in (('L','R',minimum),('R','L',minimum_r)):
        fixed=s.matcher(md,nd).compute(gray[side],gray[other])
        raw[side]=fixed.astype(np.float32)/16.;valid_raw[side]=fixed>(md-1)*16
        rt[side]=trace_refinement(colors[side],colors[other],raw[side],valid_raw[side]&support[side])
    dl=rt['L']['stages'][-1];dr=rt['R']['stages'][-1]
    require(np.array_equal(dl[sl],fresh['disparity_px']), 'left trace differs from saved refined disparity')
    require(np.array_equal(raw['L'][sl],fresh['disparity_sgbm_px']), 'left SGBM trace differs')
    require(np.array_equal(dr,fresh['disparity_right_full_px']), 'right trace differs from saved disparity')
    uv=g.pixels(w,h);ur=uv[...,0]-dl;vv=uv[...,1].astype(np.float32);xr=ur.astype(np.float32)
    rem=lambda a,method:cv2.remap(a,xr,vv,method,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    dr_at=rem(dr,cv2.INTER_LINEAR)
    vr_at=rem((valid_raw['R']&support['R']).astype(np.float32),cv2.INTER_LINEAR)>.999
    rid=rem(ids['R'].astype(np.float32),cv2.INTER_NEAREST).astype(np.int32)
    lr=np.abs(dl+dr_at)
    m=gray['L'].astype(np.float32)
    std=np.sqrt(np.maximum(cv2.boxFilter(m*m,-1,(5,5))-cv2.boxFilter(m,-1,(5,5))**2,0.))
    rect_xyz=g.reproject_q(r['Q_full'],uv,dl);lo,hi=c['depth_search_z_rect_m']
    roi=cv2.getValidDisparityROI(tuple(r['roi_L']),tuple(r['roi_R']),minimum,nd,s.BLOCK_SIZE)
    gx,gy,gw,gh=roi;region=np.zeros((h,w),bool);region[gy:gy+gh,gx:gx+gw]=True
    gates={'left_disparity_valid':valid_raw['L'], 'right_match_supported':vr_at,
           'left_supported':support['L'], 'right_in_raster':(ur>=0)&(ur<w-1),
           'lr_consistent':lr<=s.LR_TOLERANCE_PX,'same_instance':rid==ids['L'],
           'texture':std>=s.MIN_LOCAL_STD_U8,
           'finite_range_in_bounds':np.isfinite(rect_xyz).all(axis=-1)&(rect_xyz[...,2]>=lo)&(rect_xyz[...,2]<=hi),
           'disparity_roi':region}
    accepted=audit.intersect(gates)
    require(np.array_equal(accepted[sl],fresh['valid']), 'traced gate conjunction differs from frozen validity')
    require(np.array_equal(lr[sl],fresh['lr_error_px']) and np.array_equal(std[sl],fresh['left_gray_std']),
            'traced diagnostic scores differ')
    # Right-bin occupancy is approximate sampling evidence, NOT visibility truth.
    bins=np.rint(ur).astype(int);ok=accepted&(bins>=0)&(bins<w)
    count=np.zeros((h,w),np.int32);max_d=np.full((h,w),-np.inf,np.float32)
    rows=np.indices((h,w))[0]
    np.add.at(count,(rows[ok],bins[ok]),1);np.maximum.at(max_d,(rows[ok],bins[ok]),dl[ok])
    clipped=np.clip(bins,0,w-1)
    same_bin=count[rows,clipped];larger=max_d[rows,clipped]-dl
    larger=np.where(np.isfinite(larger),larger,np.nan)
    # Distances are to ID transitions, not to geometric half-occlusion limits.
    distance={}
    for side in ('L','R'):
        interior=s.mask_interior(ids[side],1)
        distance[side]=cv2.distanceTransform(interior.astype(np.uint8),cv2.DIST_L2,5)
    fields={'stages_L':rt['L']['stages'][:,sl[0],sl[1]],
            'numerator_L':rt['L']['numerator'][:,sl[0],sl[1]],
            'denominator_L':rt['L']['denominator'][:,sl[0],sl[1]],
            'unbounded_step_L':rt['L']['unbounded_step'][:,sl[0],sl[1]],
            'residual_variance_L':rt['L']['residual_variance_before_update'][:,sl[0],sl[1]],
            'right_stages_full':rt['R']['stages'],'right_id_full':ids['R'],
            'right_initial_supported_full':valid_raw['R']&support['R'],
            'right_id_boundary_distance_full':distance['R'],
            'left_id_boundary_distance':distance['L'][sl],
            'right_bin_accepted_count':same_bin[sl],
            'right_bin_max_disparity_minus_this':larger[sl],
            'right_x':xr[sl],'left_gray_full':gray['L'],'right_gray_full':gray['R'],
            'right_id_at_prediction':rid[sl], 'valid':accepted[sl]}
    fields.update({'gate_'+k:v[sl] for k,v in gates.items()})
    cycle=cycle_endpoints(dl[sl],dr,xr[sl],vv[sl])
    require(np.array_equal(np.abs(cycle['signed_residual_interpolated']),fresh['lr_error_px']),
            'cycle endpoint trace differs from production')
    fields.update({'cycle_'+k:v for k,v in cycle.items()})
    return {'fresh':fresh,'fields':fields}


def true_disparity(c: dict, result: dict, truth: dict) -> np.ndarray:
    xyz=truth['position_h'];uv=[]
    for eye,rr,pp in zip(c['eyes'],('R1','R2'),('P1','P2')):
        q=(xyz-np.asarray(eye['centre_h_m'])) @ np.asarray(eye['R_hc']) @ result[rr].T
        p=q @ result[pp][:,:3].T
        with np.errstate(divide='ignore',invalid='ignore'):uv.append(p[...,0]/p[...,2])
    return uv[0]-uv[1]


def scalar(value):
    value=value.item() if isinstance(value,np.generic) else value
    return None if isinstance(value,float) and not np.isfinite(value) else value


def fraction(mask: np.ndarray, population: np.ndarray):
    return float(np.mean(mask[population])) if np.any(population) else None


def evaluated_stages(c: dict, trace: dict, context: dict) -> tuple[dict,dict]:
    r=trace['fresh'];f=trace['fields'];truth=context['truth'];centre=context['centre']
    n=c['core_size'];uv=g.pixels(n,n);dtrue=true_disparity(c,r,truth)
    stage_xyz=[g.rect_to_head(c,r['R1'],g.reproject_q(r['Q_core'],uv,d)) for d in f['stages_L']]
    caps=cap_masks(f['stages_L'][0],f['stages_L'][-1]);reports={}
    with np.errstate(divide='ignore',invalid='ignore'):
        rel=np.array([(np.linalg.norm(p-centre,axis=-1)-truth['range_m'])/truth['range_m'] for p in stage_xyz])
    for name,ref in context['refs'].items():
        population=ref&r['valid'];stages=[]
        for i,p in enumerate(stage_xyz):
            entry=evaluate.describe_errors(p,truth,centre,population,ref)
            entry['signed_disparity_error_px']=audit.distribution((f['stages_L'][i]-dtrue)[population])
            entry['disparity_px']=audit.distribution(f['stages_L'][i][population])
            if i:
                entry['gradient_variance']=audit.distribution(f['denominator_L'][i-1][population])
                entry['unbounded_step_px']=audit.distribution(f['unbounded_step_L'][i-1][population])
                entry['step_clipped_fraction']=fraction(np.abs(f['unbounded_step_L'][i-1])>.5,population)
                entry['denominator_inactive_fraction']=fraction(f['denominator_L'][i-1]<=1e-8,population)
                entry['cumulative_cap_fraction']=fraction(np.isclose(np.abs(f['stages_L'][i]-f['stages_L'][0]),.75,rtol=0,atol=CAP_ATOL),population)
            stages.append(entry)
        bad=population&(np.abs(rel[-1])>.03);good=population&~bad
        cap_stats={label:{'count':int((population&m).sum()),'fraction_accepted':fraction(m,population),
                         'fraction_bad':fraction(m,bad),
                         'final_error':evaluate.describe_errors(stage_xyz[-1],truth,centre,population&m,ref&m)}
                   for label,m in caps.items()}
        shift=f['stages_L'][-1]-f['stages_L'][0]
        vals,counts=np.unique(f['stages_L'][-1][population],return_counts=True)
        order=np.argsort(-counts,kind='stable')[:12]
        reports[name]={'reference_pixels':int(ref.sum()),'fixed_accepted_pixels':int(population.sum()),
            'stage_metrics_DIAGNOSTIC_NOT_INSTRUMENTS':stages,'cap_groups':cap_stats,
            'refinement_shift_px':audit.distribution(shift[population]),
            'final_bad_count':int(bad.sum()),
            'raw_good_to_refined_bad_count':int((bad&(np.abs(rel[0])<=.03)).sum()),
            'raw_bad_to_refined_good_count':int((good&(np.abs(rel[0])>.03)).sum()),
            'initial_disparity_fractional_part':audit.distribution(np.mod(f['stages_L'][0][population],1)),
            'truth_disparity_fractional_part':audit.distribution(np.mod(dtrue[population],1)),
            'top_final_disparity_atoms':[{'disparity_px':float(vals[j]),'count':int(counts[j]),
                'fraction':float(counts[j]/len(f['stages_L'][-1][population]))} for j in order],
            'tail_initial_disparity':audit.distribution(f['stages_L'][0][bad]),
            'tail_final_disparity':audit.distribution(f['stages_L'][-1][bad]),
            'tail_shift':audit.distribution(shift[bad]),
            'tail_gradient_variance_by_iteration':[audit.distribution(v[bad]) for v in f['denominator_L']],
            'safe_gradient_variance_by_iteration':[audit.distribution(v[good]) for v in f['denominator_L']]}
    return reports,{'truth_disparity_px':dtrue,'signed_range_error_by_stage':rel,'xyz_final_unmasked':stage_xyz[-1]}


def leakage_table(c: dict,trace: dict,context: dict, core: np.ndarray, stage_fields: dict) -> list[dict]:
    r=trace['fresh'];f=trace['fields'];truth=context['truth'];rows=[]
    x,y,_,_=map(int,r['crop_xywh']);dr=f['right_stages_full'][-1]
    for v,u in np.argwhere(context['refs']['singly_visible']&r['valid']):
        item={'u_core':int(u),'v_core':int(v),'u_full':int(u+x),'v_full':int(v+y),
              'in_eroded_core':bool(core[v,u]),'left_instance':int(r['instance_id'][v,u]),
              'truth_instance':int(truth['instance_id'][v,u]),
              'matched_right_instance':int(f['right_id_at_prediction'][v,u]),
              'right_x_predicted':float(f['right_x'][v,u]),
              'right_x_true_surface':float(u+x-stage_fields['truth_disparity_px'][v,u]),
              'truth_disparity_px':float(stage_fields['truth_disparity_px'][v,u]),
              'truth_range_m':float(truth['range_m'][v,u]),
              'prediction_range_m':float(r['range_left_m'][v,u]),
              'truth_head_z_m':float(truth['position_h'][v,u,2]),'prediction_head_z_m':float(r['xyz_h'][v,u,2]),
              'position_error_m':float(np.linalg.norm(r['xyz_h'][v,u]-truth['position_h'][v,u])),
              'lr_error_px':float(r['lr_error_px'][v,u]),'texture_score':float(r['left_gray_std'][v,u]),
              'left_id_boundary_distance_px':float(f['left_id_boundary_distance'][v,u]),
              'right_bin_accepted_count':int(f['right_bin_accepted_count'][v,u]),
              'right_bin_max_disparity_minus_this':scalar(f['right_bin_max_disparity_minus_this'][v,u])}
        for key,arr in f.items():
            if key.startswith(('gate_','cycle_')):item[key]=scalar(arr[v,u])
        for i in range(4):item['left_d_stage_'+str(i)]=float(f['stages_L'][i,v,u])
        for i in range(3):
            item['left_gvar_'+str(i+1)]=float(f['denominator_L'][i,v,u])
            item['left_unbounded_step_'+str(i+1)]=float(f['unbounded_step_L'][i,v,u])
        for end in (0,1):
            col=int(f['cycle_x'+str(end)][v,u]);yy=v+y
            if 0<=col<dr.shape[1]:
                item[f'right_x{end}_instance']=int(f['right_id_full'][yy,col])
                item[f'right_x{end}_supported']=bool(f['right_initial_supported_full'][yy,col])
                item[f'right_x{end}_id_boundary_distance_px']=float(f['right_id_boundary_distance_full'][yy,col])
                for i in range(4):item[f'right_x{end}_d_stage_{i}']=float(f['right_stages_full'][i,yy,col])
        rows.append(item)
    return rows


def draw_visual(dest:Path,trace:dict,ctx:dict,core:np.ndarray,stage:dict,label:str)->None:
    r=trace['fresh'];f=trace['fields'];pop=ctx['refs']['interior']&r['valid']
    caps=cap_masks(f['stages_L'][0],f['stages_L'][-1]);rel=stage['signed_range_error_by_stage']
    byte=lambda z:np.rint(255*np.clip(np.nan_to_num(z,nan=0),0,1)).astype(np.uint8)
    panels=[('HDR display / same RGB',hdr.hdr_to_u8(r['rgb_left'])),('Frozen accepted interior',byte(pop)),
        ('Raw SGBM error / 3%',byte(np.where(pop,np.abs(rel[0])/.03,0))),
        ('After update 1 / 3%',byte(np.where(pop,np.abs(rel[1])/.03,0))),
        ('After update 3 / 3%',byte(np.where(pop,np.abs(rel[3])/.03,0))),
        ('At -0.75 or +0.75 cap',byte(pop&(caps['lower_cap']|caps['upper_cap']))),
        ('Truth: occlusion core',byte(core)),('Accepted in occlusion core',byte(core&r['valid'])),
        ('Cycle interpolation pass only',byte(r['valid']&f['cycle_interpolated_pass']&~f['cycle_both_endpoints_pass']))]
    size=256;head=64;line=30
    canvas=Image.new('RGB',(3*size,head+3*(size+line)),'white');draw=ImageDraw.Draw(canvas)
    draw.text((8,8),'FSG1e DIAGNOSTIC - '+label,fill='black')
    draw.text((8,30),'Stage errors use SAME final support. Black may mean missing; read masks.',fill='black')
    for i,(title,data) in enumerate(panels):
        xx=(i%3)*size;yy=head+(i//3)*(size+line);draw.text((xx+4,yy+6),title,fill='black')
        canvas.paste(Image.fromarray(data).convert('RGB').resize((size,size),Image.Resampling.NEAREST),(xx,yy+line))
    canvas.save(dest/'stage_visibility.png')


def correlation(a:np.ndarray,b:np.ndarray):
    return float(np.corrcoef(a,b)[0,1]) if a.size>=3 and np.std(a)>1e-12 and np.std(b)>1e-12 else None


def compare_seeds(a:dict,b:dict)->dict:
    require(np.array_equal(a['truth_disparity_px'],b['truth_disparity_px'],equal_nan=True),
            'seed pair geometry/reference mismatch')
    results={}
    for name in a['refs']:
        require(np.array_equal(a['refs'][name],b['refs'][name]),'seed reference mask mismatch')
        pop=a['refs'][name]&a['valid']&b['valid'];n=int(pop.sum())
        ea=a['error'][-1][pop];eb=b['error'][-1][pop]
        ba=np.abs(ea)>.03;bb=np.abs(eb)>.03;union=np.count_nonzero(ba|bb)
        results[name]={'common_accepted_pixels':n,'signed_range_error_correlation':correlation(ea,eb),
            'bad_both_count':int(np.count_nonzero(ba&bb)), 'bad_union_count':int(union),
            'bad_jaccard':float(np.count_nonzero(ba&bb)/union) if union else None,
            'seed73_minus_seed31_range_error':audit.distribution(eb-ea),
            'warning':'Same geometry/texture, two noise realizations, correlated pixels; not independent trials.'}
    return results


def verify_input_summary(folder:Path,prediction:Path)->None:
    meta=json.loads((prediction/'summary.json').read_text())
    require(set(meta.get('input_sha256',{}))=={'calibration.json','observation.npz'}, 'missing prediction input provenance')
    for name,digest in meta['input_sha256'].items():
        require(s.sha256(folder/name)==digest,'stale prediction input: '+name)
    require(meta.get('numpy')==np.__version__ and meta.get('opencv')==cv2.__version__,
            'replay requires original recorded NumPy/OpenCV; do not upgrade or weaken guard')


def audit_pair(folder:Path,pred_dirs:dict,dest:Path,is_validation:bool,allow_synthetic:bool=False)->tuple[dict,dict]:
    require(not dest.exists(),'pair audit output exists')
    c,obs=hdr.read_observation(folder);acq=json.loads((folder/'acquisition.json').read_text())
    real=acq.get('source')=='blender_cycles' and acq.get('checks',{}).get('independent_blender_checks') is True
    require(real or (allow_synthetic and acq.get('source')=='synthetic_stub'),'checked Blender record required')
    traces={}
    for instrument,path in pred_dirs.items():
        verify_input_summary(folder,path)
        stored=audit.load_npz(path/'result.npz')
        traces[instrument]=trace_rgb(c,obs,stored,instrument)
        d=dest/instrument;d.mkdir(parents=True)
        np.savez_compressed(d/'rgb_trace_DIAGNOSTIC.npz',**traces[instrument]['fields'])
    # Only after BOTH exact RGB-only traces have been persisted is truth opened.
    mesh=audit.load_npz(folder/'evaluation_only'/'mesh.npz')
    if is_validation:spec.validate_mesh(folder.name,mesh)
    reports={};cross={}
    for instrument,trace in traces.items():
        d=dest/instrument
        official,ctx=paired.candidate_evaluation(c,trace['fresh'],mesh,bool(real),allow_synthetic)
        mono=ctx['refs']['singly_visible']
        if is_validation:core,desc=validation.occlusion_reference(folder.name,c['profile'],mono)
        else:
            core=np.zeros_like(mono);desc={'status':'NOT_EXERCISED' if not np.any(mono) else 'RAW_ONLY',
                'reference_pixels':int(mono.sum()),'core_pixels':0,'erosion_radius_px':None}
        stages,fields=evaluated_stages(c,trace,ctx)
        leaks=leakage_table(c,trace,ctx,core,fields)
        report={'instrument':instrument,'original_numerical_metrics':official,'stages':stages,
            'occlusion':validation.occlusion_result(trace['fresh']['valid'],mono,core,desc),
            'all_accepted_singly_visible_pixels':leaks,'trace_saved_before_truth':True,'exact_replay':True,
            'no_acceptance_change':True,'diagnostic_only':True,'new_primary_samples':0,
            'cycle_endpoint_warning':'Right-bin competition and endpoint checks are descriptive, not proposed rejection masks.'}
        g.json_write(d/'audit.json',report)
        keys=sorted({k for row in leaks for k in row})
        with (d/'accepted_occlusions.csv').open('w',newline='') as fh:
            writer=csv.DictWriter(fh,fieldnames=keys or ['NO_ACCEPTED_SINGLY_VISIBLE_PIXELS']);writer.writeheader();writer.writerows(leaks)
        np.savez_compressed(d/'evaluation_DIAGNOSTIC.npz',**{k:v for k,v in fields.items() if k!='xyz_final_unmasked'},
                            interior=ctx['refs']['interior'],occlusion_core=core,singly_visible=mono)
        draw_visual(d,trace,ctx,core,fields,folder.name+'/'+instrument)
        reports[instrument]=report
        cross[instrument]={'truth_disparity_px':fields['truth_disparity_px'],'refs':ctx['refs'],
            'error':fields['signed_range_error_by_stage'],'valid':trace['fresh']['valid']}
        for name,v in stages.items():
            if name.startswith('instance_'):
                z=v['stage_metrics_DIAGNOSTIC_NOT_INSTRUMENTS']
                print(f"[fsg-failure-audit] {folder.parent.name}/{folder.name}/{instrument}/{name} "
                      f"n={v['fixed_accepted_pixels']} raw_p95={z[0]['p95_relative_range_error']} "
                      f"final_p95={z[-1]['p95_relative_range_error']} final_bad={v['final_bad_count']} "
                      f"lower_cap={v['cap_groups']['lower_cap']['count']} upper_cap={v['cap_groups']['upper_cap']['count']}")
        print(f"[fsg-failure-audit] {folder.parent.name}/{folder.name}/{instrument} "
              f"accepted_mono={len(leaks)} accepted_core={report['occlusion']['accepted_core']}")
    return reports,cross


def run_audit(development:Path,development_results:Path,validation_runs:list[Path],validation_results:Path,
              out:Path,allow_synthetic:bool=False)->dict:
    start=time.perf_counter();frozen=check_sources()
    own={p.name:s.sha256(p) for p in (Path(__file__),Path(__file__).parent/'dev'/'check_fsg_failure_audit.py')}
    roots=[development,*validation_runs,development_results,validation_results]
    roots,out=audit.validate_paths(roots,out)
    development,*other=roots;validation_runs=other[:2];development_results,validation_results=other[2:]
    require(len(validation_runs)==2,'two validation runs required')
    dm=json.loads((development/'run.json').read_text())
    require(dm.get('complete') and dm.get('profile')=='full' and dm.get('seed')==17 and dm.get('spp')==256
            and set(dm.get('cases',[]))=={'fronto','tilted','step'},'requires unchanged full seed-17 development run')
    metas=[validation.read_run(p,allow_synthetic) for p in validation_runs];validation.validate_schedule(metas,'full')
    before=paired.snapshot(roots);result={};seeds={}
    try:
        for name in dm['cases']:
            folder=development/name;pred={'legacy':folder/'stereo',
                'hdr':development_results/development.name/name/'stereo_candidate'}
            result[development.name+'/'+name],_=audit_pair(folder,pred,out/development.name/name,False,allow_synthetic)
        for run,meta in zip(validation_runs,metas):
            seeds[meta['seed']]={}
            for name in spec.CASES:
                base=validation_results/run.name/name
                pred={'legacy':base/'stereo_legacy','hdr':base/'stereo_candidate'}
                key=run.name+'/'+name
                result[key],seeds[meta['seed']][name]=audit_pair(run/name,pred,out/run.name/name,True,allow_synthetic)
        cross={name:{i:compare_seeds(seeds[31][name][i],seeds[73][name][i]) for i in ('legacy','hdr')}
               for name in spec.CASES}
    finally:
        require(paired.snapshot(roots)==before,'inputs changed during audit; discard interpretation')
        require(check_sources()==frozen,'frozen sources changed during audit')
        require(all(s.sha256(Path(__file__) if n==Path(__file__).name else Path(__file__).parent/'dev'/n)==v
                    for n,v in own.items()),'audit sources changed during execution')
    real=all(m.get('source')=='blender_cycles' for m in [dm,*metas])
    report={'schema':AUDIT_ID,'status':'AUDIT_COMPLETE_NOT_A_MILESTONE' if real else 'SYNTHETIC_AUDIT_NOT_A_RENDER_RESULT',
            'pairs':result,'cross_seed':cross,'diagnostic_only':True,'new_primary_samples':0,'inputs_unchanged':True,
            'input_sha256':before,'frozen_sources':frozen,'audit_sources':own,'seconds':time.perf_counter()-start,
            'full_profile_milestone_pass':False,'adopted_default':False,'fusion_authorized':False,
            'warning':'No new candidate. Stage scores condition on the original FINAL accepted support. '
                      'Truth-conditioned cohorts and visibility labels are evaluation only. Reused validation is now diagnostic data.'}
    g.json_write(out/'audit.json',report)
    print(f"[fsg-failure-audit] SUMMARY pairs={len(result)} exact_replay=true inputs_unchanged=true "
          f"new_primary_samples=0 seconds={report['seconds']:.3f} status={report['status']}")
    return report


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--development',type=Path,required=True);ap.add_argument('--development-results',type=Path,required=True)
    ap.add_argument('--validation',type=Path,nargs=2,required=True);ap.add_argument('--validation-results',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--allow-synthetic',action='store_true')
    args=ap.parse_args();run_audit(args.development,args.development_results,args.validation,args.validation_results,args.out,args.allow_synthetic)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'[fsg-failure-audit] FAIL {type(exc).__name__}: {exc}',file=sys.stderr);raise SystemExit(1)
