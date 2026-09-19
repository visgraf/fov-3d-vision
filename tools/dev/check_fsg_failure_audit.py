"""FSG1e software checks. No Blender or scene assets; not measurement evidence."""
from __future__ import annotations
import argparse
import contextlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
import numpy as np
import cv2
TOOLS=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(TOOLS),str(TOOLS/'dev')]
import fsg_failure_audit as a
import fsg_geometry as g
import fsg_stereo as s
import fsg_stereo_hdr as hdr
import fsg_render as render
import fsg_hdr_compare as paired
import fsg_validation_eval as ev
import check_fsg_validation as vc
from fake_blender_fsg import SyntheticBackend


def require(ok,message='assertion'):
    if not ok:raise AssertionError(message)


def raises(kind,fn):
    try:fn()
    except kind:return
    raise AssertionError('expected '+kind.__name__)


def cap_control(bad=False):
    initial=np.array([24.,24.,24.],np.float32)
    final=np.array([23.25,24.75,24.],np.float32)
    groups=a.cap_masks(initial,final)
    if bad:groups['lower_cap']=groups['upper_cap'].copy()
    require(groups['lower_cap'].tolist()==[True,False,False], 'lower-cap classification lost its sign')
    require(groups['upper_cap'].tolist()==[False,True,False], 'upper-cap classification lost its sign')
    require(np.all(sum(v.astype(int) for v in groups.values())==1),'cap partition overlaps or misses pixels')


def replay_control():
    expected={'valid':np.array([True]),'disparity':np.array([24.],np.float32)}
    actual={'valid':np.array([True]),'disparity':np.array([23.25],np.float32)}
    a.audit.assert_replay(expected,actual)


def cycle_control(bad=False):
    # Both endpoint cycles are wrong, their interpolation is exactly consistent.
    dr=np.array([[-8.,-12.,-10.]],np.float32)
    result=a.cycle_endpoints(np.array([[10.]],np.float32),dr,np.array([[.5]],np.float32),np.array([[0.]],np.float32))
    require(result['interpolated_pass'][0,0], 'known interpolated cycle should pass')
    require(not result['both_endpoints_pass'][0,0], 'known wrong endpoints should fail separately')
    if bad:require(result['both_endpoints_pass'][0,0], 'interpolated consistency does not establish endpoint consistency')


def make_development(path:Path,profile='full'):
    args=render.parse_args(['--out',str(path),'--profile',profile,'--seed','17',
                            '--spp',str({'small':64,'full':256}[profile])])
    render.acquire(args,SyntheticBackend())
    for name in ('fronto','tilted','step'):s.process_pair(path/name)


def self_test()->dict:
    start=time.perf_counter();checks=[];detail=io.StringIO()
    def check(name,fn):
        try:fn();checks.append({'name':name,'pass':True});print('[fsg-failure-check] PASS',name)
        except Exception as exc:checks.append({'name':name,'pass':False,'error':repr(exc)});print('[fsg-failure-check] FAIL',name,repr(exc))
    check('eleven pinned source files unchanged',a.check_sources)
    check('cap sign and disjoint partition known answer',cap_control)
    check('cap negative fails',lambda:raises(AssertionError,lambda:cap_control(True)))
    check('stale replay negative fails',lambda:raises(ValueError,replay_control))
    check('interpolated-cycle cancellation is distinguished',cycle_control)
    check('false endpoint inference negative fails',lambda:raises(AssertionError,lambda:cycle_control(True)))
    d=abs(s.rectification(g.make_calibration('full'))['P2'][0,3])/3.2
    check('geometric disparity at 3.2m known answer',lambda:require(abs(d-23.97619842464091)<1e-9))
    check('reported tail matches hypothetical lower cap arithmetic',lambda:require(abs((d/23.25-1)-.031234338696499123)<3e-9))
    rng=np.random.default_rng(741)
    left=rng.uniform(.01,3.,(28,32,3)).astype(np.float32)
    right=np.roll(left,-3,axis=1)+rng.normal(0,.01,left.shape).astype(np.float32)
    init=np.full((28,32),3.2,np.float32);support=rng.uniform(size=init.shape)>.15
    rt=a.trace_refinement(left,right,init,support)
    check('instrumented refiner exactly equals frozen result',lambda:require(np.array_equal(rt['stages'][-1],s.refine_disparity(left,right,init,support))))
    check('all four stages retained',lambda:require(rt['stages'].shape==(4,28,32)))
    check('unsupported disparities remain initial',lambda:require(np.all(rt['stages'][:,~support]==init[~support])))
    check('refinement trace bounded by original cap',lambda:require(np.max(np.abs(rt['stages']-init))<=.750001))
    flat=np.ones_like(left)
    zero=a.trace_refinement(flat,flat,init,np.ones_like(support))
    check('flat signal does not gain invented disparity updates',lambda:require(np.all(zero['stages']==init)))
    check('zero denominators remain visible in trace',lambda:require(np.all(zero['denominator']==0)))
    check('initial stage preserved exactly',lambda:require(np.array_equal(rt['stages'][0],init)))
    check('constant error correlation is undefined, not perfect',lambda:require(a.correlation(np.ones(5),np.ones(5)) is None))
    check('empty cap population yields null not zero rate',lambda:require(a.fraction(np.zeros(3,bool),np.zeros(3,bool)) is None))
    with tempfile.TemporaryDirectory(prefix='fsg1e-test-') as t:
        root=Path(t);run=root/'small31'
        with contextlib.redirect_stdout(detail):vc.make_synthetic(run)
        folder=run/'step_right';pred=root/'saved'
        with contextlib.redirect_stdout(detail):ev.infer_pair(folder,pred)
        paths={'legacy':pred/'stereo_legacy','hdr':pred/'stereo_candidate'}
        before=paired.snapshot([run,pred])
        with contextlib.redirect_stdout(detail):report,cross=a.audit_pair(folder,paths,root/'audit',True,True)
        check('synthetic audit input bytes preserved',lambda:require(paired.snapshot([run,pred])==before))
        check('both estimators replayed exactly',lambda:require(all(v['exact_replay'] for v in report.values())))
        check('RGB traces saved before any geometry access',lambda:require(all(v['trace_saved_before_truth'] for v in report.values())))
        check('both visual reports written',lambda:require(all((root/'audit'/i/'stage_visibility.png').is_file() for i in paths)))
        check('no point cloud or new accepted geometry exported',lambda:require(not list((root/'audit').rglob('*.ply'))))
        check('historical support is unchanged at all diagnostic stages',lambda:require(all(
            len({m['accepted_pixels'] for m in group['stage_metrics_DIAGNOSTIC_NOT_INSTRUMENTS']})==1
            for ir in report.values() for group in ir['stages'].values())))
        check('stage final metrics reproduce independent current evaluator',lambda:require(all(
            np.isclose(group['stage_metrics_DIAGNOSTIC_NOT_INSTRUMENTS'][-1]['median_relative_range_error'],
                       ir['original_numerical_metrics']['metrics'][key]['median_relative_range_error'],rtol=0,atol=1e-6)
            for ir in report.values() for key,group in ir['stages'].items()
            if ir['original_numerical_metrics']['metrics'][key]['median_relative_range_error'] is not None)))
        check('same-frame truth disparity agrees with ideal reconstruction',lambda:require(np.isfinite(cross['hdr']['truth_disparity_px']).all()))
        equal=a.compare_seeds(cross['hdr'],cross['hdr'])
        check('same-record seed comparison has zero difference',lambda:require(
            equal['instance_1_interior']['seed73_minus_seed31_range_error']['quantiles']['max']==0))
        wrong={**cross['hdr'],'truth_disparity_px':cross['hdr']['truth_disparity_px']+.1}
        check('seed geometry mismatch rejected',lambda:raises(ValueError,lambda:a.compare_seeds(cross['hdr'],wrong)))
        check('new audit refuses overwrite',lambda:raises(ValueError,lambda:a.audit_pair(folder,paths,root/'audit',True,True)))
        check('synthetic observations forbidden in real mode',lambda:raises(ValueError,lambda:a.audit_pair(folder,paths,root/'bad-real',True)))
        c,obs=hdr.read_observation(folder);stored=a.audit.load_npz(paths['hdr']/'result.npz')
        truth=folder/'evaluation_only';hidden=folder/'hidden';truth.rename(hidden)
        try:
            trace=a.trace_rgb(c,obs,stored,'hdr')
            check('RGB trace has no dependency on evaluation geometry',lambda:a.audit.assert_replay(stored,trace['fresh']))
        finally:hidden.rename(truth)
        old=dict(stored);old['disparity_px']=stored['disparity_px'].copy();old['disparity_px'][0,0]+=.125
        # Exercise leakage reporting even when analytic stereo has zero leaks.
        trace=a.trace_rgb(c,obs,stored,'hdr')
        mesh=a.audit.load_npz(truth/'mesh.npz')
        _,ctx=paired.candidate_evaluation(c,stored,mesh,False,True)
        core,_=ev.occlusion_reference('step_right','small',ctx['refs']['singly_visible'])
        _,sf=a.evaluated_stages(c,trace,ctx)
        v,u=np.argwhere(core)[0]
        injected={k:val.copy() for k,val in stored.items()}
        injected['valid'][v,u]=True;injected['xyz_h'][v,u]=sf['xyz_final_unmasked'][v,u]
        injected['range_left_m'][v,u]=np.linalg.norm(injected['xyz_h'][v,u]-ctx['centre'])
        fake_trace={**trace,'fresh':injected}
        leaks=a.leakage_table(c,fake_trace,ctx,core,sf)
        check('injected single leak is fully enumerated',lambda:require(any(row['u_core']==u and row['v_core']==v and row['in_eroded_core'] for row in leaks)))
        check('leak row retains actual gate and cycle fields',lambda:require(all('gate_same_instance' in row and 'cycle_signed_residual_x0' in row for row in leaks)))
        check('leak serialization permits no NaN/Infinity',lambda:json.dumps(leaks,allow_nan=False))
        check('one changed saved disparity fails replay',lambda:raises(ValueError,lambda:a.trace_rgb(c,obs,old,'hdr')))
        p=paths['hdr']/'summary.json';original=p.read_bytes();meta=json.loads(original);meta['input_sha256']['observation.npz']='bad';g.json_write(p,meta)
        try:check('stale RGB fingerprint rejected',lambda:raises(ValueError,lambda:a.verify_input_summary(folder,paths['hdr'])))
        finally:p.write_bytes(original)
        meta=json.loads(original);meta['numpy']='0';g.json_write(p,meta)
        try:check('different replay environment rejected',lambda:raises(ValueError,lambda:a.verify_input_summary(folder,paths['hdr'])))
        finally:p.write_bytes(original)
        check('final preservation after all negative tests',lambda:require(paired.snapshot([run,pred])==before))
    passed=sum(x['pass'] for x in checks)
    result={'passed':passed,'failed':len(checks)-passed,'seconds':time.perf_counter()-start,
        'checks':checks,'blender_executed':False,'detail_log':detail.getvalue(),
        'note':'Synthetic checks test audit correctness; not the reported cap population or real occlusion leaks.'}
    print(f"[fsg-failure-check] SUMMARY passed={passed} failed={result['failed']} seconds={result['seconds']:.3f} blender_executed=False")
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__);m=ap.add_mutually_exclusive_group(required=True)
    m.add_argument('--self-test',action='store_true');m.add_argument('--negative',choices=('cap','replay','cycle'))
    ap.add_argument('--report',type=Path);args=ap.parse_args()
    if args.negative:
        {'cap':lambda:cap_control(True),'replay':replay_control,'cycle':lambda:cycle_control(True)}[args.negative]()
        raise AssertionError('negative unexpectedly passed')
    result=self_test()
    if args.report:g.json_write(args.report,result)
    raise SystemExit(bool(result['failed']))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'[fsg-failure-check] FAIL {type(exc).__name__}: {exc}',file=sys.stderr);raise SystemExit(1)
