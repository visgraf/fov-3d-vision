"""FSG1f: one frozen candidate and predefined controls on seven EXISTING pairs.
No rendering, parameter sweep, default adoption or fusion. Saved baselines must
replay exactly. All newly inferred records are persisted before truth is read.
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
import fsg_stereo_supported as candidate
import fsg_failure_audit as stages
import fsg_coverage_audit as audit
import fsg_hdr_compare as paired
import fsg_validation_scene as spec
import fsg_validation_eval as validation
import fsg_evaluate as e
require=audit.require


def check_sources() -> dict:
    sources=stages.check_sources();candidate.check_kernel_equivalence()
    root=Path(__file__).resolve().parent
    return dict(sources,**{name:s.sha256(root/name) for name in
        ('fsg_failure_audit.py','fsg_stereo_supported.py','fsg_supported_compare.py',
         'dev/check_fsg_supported.py')})


def support_comparison(old: dict, new: dict, context: dict) -> dict:
    result={};ov=old['valid'];nv=new['valid'];truth=context['truth'];centre=context['centre']
    for name,ref in context['refs'].items():
        masks={'common':ref&ov&nv,'gained':ref&~ov&nv,'lost':ref&ov&~nv,'neither':ref&~ov&~nv}
        require(sum(int(m.sum()) for m in masks.values())==int(ref.sum()),'support partition failed')
        result[name]={'reference_pixels':int(ref.sum()),'counts':{k:int(v.sum()) for k,v in masks.items()},
            'common_old':e.describe_errors(old['xyz_h'],truth,centre,masks['common'],masks['common']),
            'common_new':e.describe_errors(new['xyz_h'],truth,centre,masks['common'],masks['common']),
            'gained_new':e.describe_errors(new['xyz_h'],truth,centre,masks['gained'],masks['gained']),
            'lost_old':e.describe_errors(old['xyz_h'],truth,centre,masks['lost'],masks['lost'])}
    return result



def evaluate_on_context(result: dict, context: dict, real: bool, allow_synthetic: bool) -> dict:
    """Reuse one frozen reference; exactly the original numerical gate arithmetic.

    Ray/mesh intersection is expensive and independent of the prediction. Software
    tests compare this result against paired.candidate_evaluation independently.
    """
    truth,refs,centre=context['truth'],context['refs'],context['centre']
    require(result['xyz_h'].shape==truth['position_h'].shape,'candidate/reference shape mismatch')
    metrics={key:e.describe_errors(result['xyz_h'],truth,centre,result['valid'],ref)
             for key,ref in refs.items()}
    fails=e.gate(metrics['interior'])
    for key in refs:
        if key.startswith('instance_') and metrics[key]['reference_pixels']>=100:
            fails += [f'{key}: {x}' for x in e.gate(metrics[key])]
    wrong=(result['instance_id']!=truth['instance_id'])&result['valid']&refs['jointly_visible_all']
    if np.any(wrong&~refs['boundary']):fails.append('accepted interior has incorrect object identity')
    if not real and not allow_synthetic:fails.append('not a checked Blender measurement')
    return {'metrics':metrics,'fails':fails,'checks_pass':not fails,
            'wrong_instance_accepted_count':int(wrong.sum()),
            'reference_status':{key:'EXERCISED' if ref.any() else 'NOT_EXERCISED' for key,ref in refs.items()}}


def occlusion_info(name: str, c: dict, context: dict, is_validation: bool) -> tuple:
    mono=context['refs']['singly_visible']
    if is_validation:core,desc=validation.occlusion_reference(name,c['profile'],mono)
    else:
        core=np.zeros_like(mono);desc={'status':'NOT_EXERCISED' if not mono.any() else 'RAW_ONLY',
            'reference_pixels':int(mono.sum()),'core_pixels':0,'erosion_radius_px':None}
    return mono,core,desc


def combined_gates(official: dict, occlusion: dict) -> list[str]:
    fails=list(official['fails'])
    if occlusion['checks_pass'] is False:
        fails.append(f"accepted {occlusion['accepted_core']} singly-visible core pixels; limit=0")
    return fails


def draw_visual(dest: Path, records: dict, context: dict, core: np.ndarray, title: str) -> None:
    interior=context['refs']['interior'];truth=context['truth'];centre=context['centre']
    def byte(a):return np.rint(255*np.clip(np.nan_to_num(a,nan=0.),0.,1.)).astype(np.uint8)
    names=('hdr_baseline',*candidate.VARIANTS);size=224;line=30;top=55
    canvas=Image.new('RGB',(4*size,4*(size+line)+top),'white');draw=ImageDraw.Draw(canvas)
    draw.text((8,8),'FSG1f EXISTING-RECORD COMPARISON: '+title,fill='black')
    draw.text((8,28),'Error black may mean missing. Controls are not selectable winners.',fill='black')
    for col,name in enumerate(names):
        r=records[name]
        with np.errstate(invalid='ignore',divide='ignore'):
            error=np.abs(np.linalg.norm(r['xyz_h']-centre,axis=-1)-truth['range_m'])/truth['range_m']
        panels=[(name,hdr.hdr_to_u8(r['rgb_left'])),('Validity, all pixels',byte(r['valid'])),
                ('Interior error / 3%',byte(np.where(r['valid']&interior,error/.03,0))),
                ('Unsafe accepted occlusion core',byte(r['valid']&core))]
        for row,(label,data) in enumerate(panels):
            x,y=col*size,top+row*(size+line);draw.text((x+4,y+6),label,fill='black')
            canvas.paste(Image.fromarray(data).convert('RGB').resize((size,size),Image.Resampling.NEAREST),(x,y+line))
    canvas.save(dest/'supported_comparison.png')


def compare_pair(folder: Path, predictions: dict, dest: Path, is_validation: bool,
                 allow_synthetic: bool=False) -> dict:
    require(not dest.exists(),'pair output already exists')
    c,obs=hdr.read_observation(folder);acq=json.loads((folder/'acquisition.json').read_text())
    real=acq.get('source')=='blender_cycles' and acq.get('checks',{}).get('independent_blender_checks') is True
    require(real or (allow_synthetic and acq.get('source')=='synthetic_stub'),'checked Blender record required')
    old={}
    for name,path in predictions.items():
        stages.verify_input_summary(folder,path)
        stored=audit.load_npz(path/'result.npz')
        fresh,_=(s.compute(c,obs) if name=='legacy' else hdr.compute_candidate(c,obs))
        audit.assert_replay(stored,fresh);old[name]=fresh
    require(set(old)=={'legacy','hdr'},'both saved baselines are required')
    records,metadata,fields=candidate.compute_variants(c,obs)
    fingerprints={n:s.sha256(folder/n) for n in ('calibration.json','observation.npz')}
    for name in candidate.VARIANTS:
        metadata[name].update(input_sha256=fingerprints,source_record=str(folder))
        hdr.save_candidate(dest/name,c,records[name],metadata[name])
    np.savez_compressed(dest/'rgb_acceptance_trace.npz',**fields)
    # TRUTH BARRIER: all three fresh RGB-only predictions already exist on disk.
    mesh=audit.load_npz(folder/'evaluation_only'/'mesh.npz')
    if is_validation:spec.validate_mesh(folder.name,mesh)
    _,context=paired.candidate_evaluation(c,old['hdr'],mesh,bool(real),allow_synthetic)
    mono,core,description=occlusion_info(folder.name,c,context,is_validation)
    instruments={'legacy_baseline':old['legacy'],'hdr_baseline':old['hdr'],**records}
    reports={}
    for name,result in instruments.items():
        official=evaluate_on_context(result,context,bool(real),allow_synthetic)
        for ident in sorted(set(mesh['instance_ids'].tolist())):
            require(official['metrics'][f'instance_{ident}_interior']['reference_pixels']>=100,
                    'required instance reference not exercised')
        occlusion=validation.occlusion_result(result['valid'],mono,core,description)
        fails=combined_gates(official,occlusion)
        reports[name]={'evaluation':official,'occlusion':occlusion,'fails':fails,'checks_pass':not fails}
        for key,m in official['metrics'].items():
            if key.startswith('instance_'):
                print(f"[fsg-supported-compare] {folder.parent.name}/{folder.name}/{name}/{key} "
                    f"coverage={m['coverage']} median={m['median_relative_range_error']} p95={m['p95_relative_range_error']}")
        for fail in fails:print(f'[fsg-supported-compare] NUMERICAL_FAIL {folder.name}/{name}: {fail}')
    contrasts={
        'hdr_to_one_step':support_comparison(old['hdr'],records['one_step_control'],context),
        'one_step_to_endpoints':support_comparison(records['one_step_control'],records['endpoint_control'],context),
        'endpoints_to_candidate':support_comparison(records['endpoint_control'],records['candidate'],context),
        'hdr_to_candidate':support_comparison(old['hdr'],records['candidate'],context)}
    # Track all baseline leaks AND any new leaks. No tiny cohort disappears in a pooled score.
    leaks=[];union=np.zeros_like(mono)
    for r in instruments.values():union |= r['valid']&mono
    x,y,_,_=map(int,records['candidate']['crop_xywh'])
    for v,u in np.argwhere(union):
        row={'u_core':int(u),'v_core':int(v),'u_full':int(u+x),'v_full':int(v+y),'in_core':bool(core[v,u])}
        for name,r in instruments.items():
            valid=bool(r['valid'][v,u]);row[name+'_accepted']=valid
            row[name+'_disparity_px']=float(r['disparity_px'][v,u])
            row[name+'_position_error_m']=(float(np.linalg.norm(r['xyz_h'][v,u]-context['truth']['position_h'][v,u])) if valid else None)
        for key in ('endpoint_left','footprint_left','right_footprint_at_match','supported_cycle','one_step_valid'):
            row[key]=bool(fields[key][v,u])
        row['max_active_endpoint_residual']=float(fields['max_active_endpoint_residual'][v,u])
        row['endpoint_weight1']=float(fields['endpoint_weight1'][v,u]);leaks.append(row)
    keys=sorted({key for row in leaks for key in row})
    with (dest/'occlusion_tracking.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=keys or ['NO_ACCEPTED_SINGLY_VISIBLE_POINTS']);writer.writeheader();writer.writerows(leaks)
    populations={}
    for key,ref in context['refs'].items():
        one=records['one_step_control']['valid'];end=records['endpoint_control']['valid'];final=records['candidate']['valid']
        masks={'one_step_accepted':ref&one,'rejected_by_endpoints':ref&one&~end,
               'rejected_by_footprint':ref&end&~final,'candidate_accepted':ref&final}
        require(int(masks['one_step_accepted'].sum())==sum(int(masks[k].sum()) for k in
                ('rejected_by_endpoints','rejected_by_footprint','candidate_accepted')),'acceptance partition failed')
        populations[key]={k:int(m.sum()) for k,m in masks.items()}
        populations[key]['first_update_shift_accepted']=audit.distribution(fields['refinement_shift_px'][ref&one])
    report={'candidate_id':candidate.CANDIDATE_ID,'case':folder.name,'real_blender_source':bool(real),
        'instruments':reports,'contrasts':contrasts,'acceptance_populations':populations,
        'all_leak_locations':leaks,'exact_legacy_and_hdr_replay':True,'predictions_saved_before_truth':True,
        'same_fixed_references':True,'candidate_checks_pass':reports['candidate']['checks_pass'],
        'controls_are_not_automatic_fallbacks':True,'new_primary_samples':0,
        'full_profile_milestone_pass':False,'adopted_default':False,'fusion_authorized':False}
    g.json_write(dest/'comparison.json',report)
    np.savez_compressed(dest/'evaluation_masks.npz',interior=context['refs']['interior'],
                        boundary=context['refs']['boundary'],singly_visible=mono,occlusion_core=core)
    draw_visual(dest,instruments,context,core,folder.parent.name+'/'+folder.name)
    return report


def compare(development:Path,development_results:Path,validation_runs:list[Path],validation_results:Path,
            out:Path,allow_synthetic:bool=False) -> dict:
    start=time.perf_counter();frozen=check_sources()
    roots,out=audit.validate_paths([development,*validation_runs,development_results,validation_results],out)
    development,*other=roots;validation_runs=other[:2];development_results,validation_results=other[2:]
    dm=json.loads((development/'run.json').read_text())
    require(dm.get('complete') and dm.get('profile')=='full' and dm.get('seed')==17 and dm.get('spp')==256
        and set(dm.get('cases',[]))=={'fronto','tilted','step'},'requires unchanged development full seed17')
    require(dm.get('source')=='blender_cycles' or (allow_synthetic and dm.get('source')=='synthetic_stub'),'development provenance')
    metas=[validation.read_run(p,allow_synthetic) for p in validation_runs];validation.validate_schedule(metas,'full')
    before=paired.snapshot(roots);reports={}
    try:
        for name in dm['cases']:
            pred={'legacy':development/name/'stereo','hdr':development_results/development.name/name/'stereo_candidate'}
            reports[development.name+'/'+name]=compare_pair(development/name,pred,out/development.name/name,False,allow_synthetic)
        for run in validation_runs:
            for name in spec.CASES:
                base=validation_results/run.name/name;pred={'legacy':base/'stereo_legacy','hdr':base/'stereo_candidate'}
                reports[run.name+'/'+name]=compare_pair(run/name,pred,out/run.name/name,True,allow_synthetic)
    finally:
        require(paired.snapshot(roots)==before,'input files changed during comparison; discard interpretation')
        require(check_sources()==frozen,'source files changed during comparison')
    passed=all(r['candidate_checks_pass'] for r in reports.values())
    real=all(r['real_blender_source'] for r in reports.values())
    status=('CANDIDATE_PASS_ON_DIAGNOSTIC_RECORDS' if passed else 'CANDIDATE_FAIL_ON_DIAGNOSTIC_RECORDS') if real else 'SYNTHETIC_COMPARISON_NOT_A_RENDER_RESULT'
    report={'schema':'FSG1f-comparison-v1','candidate_id':candidate.CANDIDATE_ID,'status':status,
        'pairs':reports,'candidate_all_gates_pass':passed,'real_blender_records':real,'input_sha256':before,
        'inputs_unchanged':True,'sources':frozen,'numpy':np.__version__,'opencv':cv2.__version__,
        'seconds':time.perf_counter()-start,'new_primary_samples':0,'development_data_only':True,
        'full_profile_milestone_pass':False,'adopted_default':False,'fusion_authorized':False,
        'limitations':'One step is selected from diagnostic evidence, not proven optimal. Footprint support may reject correct '
            'interiors or thin surfaces. A spatially coherent wrong reciprocal field can pass. Seven reused pairs are not '
            'new validation. Controls are reported, not automatically selected.'}
    g.json_write(out/'comparison.json',report)
    print(f"[fsg-supported-compare] SUMMARY pairs={len(reports)} candidate_checks_pass={str(passed).lower()} "
          f"inputs_unchanged=true new_primary_samples=0 seconds={report['seconds']:.3f} status={status}")
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--development',type=Path,required=True);ap.add_argument('--development-results',type=Path,required=True)
    ap.add_argument('--validation',type=Path,nargs=2,required=True);ap.add_argument('--validation-results',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True);ap.add_argument('--allow-synthetic',action='store_true')
    args=ap.parse_args();r=compare(args.development,args.development_results,args.validation,args.validation_results,args.out,args.allow_synthetic)
    raise SystemExit(0 if r['candidate_all_gates_pass'] else 2)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'[fsg-supported-compare] FAIL {type(exc).__name__}: {exc}',file=sys.stderr);raise SystemExit(1)
