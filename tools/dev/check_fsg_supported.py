"""Fail-capable software checks for FSG1f. No real Blender execution."""
from __future__ import annotations
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import numpy as np
import cv2
TOOLS=Path(__file__).resolve().parents[1];sys.path[:0]=[str(TOOLS),str(TOOLS/'dev')]
import fsg_geometry as g
import fsg_stereo as s
import fsg_stereo_hdr as hdr
import fsg_stereo_supported as f
import fsg_supported_compare as comparison
import fsg_coverage_audit as audit
import fsg_hdr_compare as paired
import fsg_failure_audit as stages
import fsg_validation_eval as validation
import check_fsg_validation as fixtures


def require(ok, text='assertion'):
    if not ok:raise AssertionError(text)


def raises(cls,fn):
    try:fn()
    except cls:return
    raise AssertionError('expected '+cls.__name__)


def iteration_control(bad=False):
    rng=np.random.default_rng(1721)
    l=rng.uniform(.1,2.,(30,40,3)).astype(np.float32)
    r=np.roll(l,-3,axis=1)+rng.normal(0,.01,l.shape).astype(np.float32)
    d=np.full((30,40),3.3,np.float32);ok=np.ones_like(d,bool)
    trace=stages.trace_refinement(l,r,d,ok)
    got=s.refine_disparity(l,r,d,ok) if bad else f.refine_once(l,r,d,ok)
    require(np.array_equal(got,trace['stages'][1]),'first update must equal stage 1, not the old three-update result')


def cycle_control(bad=False):
    shape=(7,40);a=np.full(shape,10.5,np.float32);b=np.full(shape,-10.5,np.float32)
    good=np.ones(shape,bool);ids=np.ones(shape,np.int32)
    b[3,9]=-8.5;b[3,10]=-12.5
    old=a[3,20]+.5*(b[3,9]+b[3,10])
    require(old==0,'known interpolated cancellation')
    ep=f.endpoint_cycle(a,b,good,good,ids,ids)
    if bad:require(ep['ok'][3,20],'averaged cancellation must not pass the endpoint gate')
    else:require(not ep['ok'][3,20],'opposite endpoint residuals accepted')


def isolated_state():
    shape=(15,40);a=np.full(shape,10.,np.float32);b=np.full(shape,-10.,np.float32)
    good=np.ones(shape,bool);ids=np.ones(shape,np.int32)
    # A false pair has a PERFECT single-endpoint cycle, surrounded by a different
    # correspondence field. No IDs or collision counts expose this pair.
    a[7,20]=8.;b[7,12]=-8.
    return dict(disparity_left=a,disparity_right=b,valid_left=good,valid_right=good,
                support_left=good,support_right=good,ids_left=ids,ids_right=ids)


def footprint_control(bad=False):
    r=f.supported_cycles(isolated_state())
    require(r['endpoint_left'][7,20],'isolated wrong pair must really be endpoint-consistent')
    if bad:require(r['supported_cycle'][7,20],'isolated endpoint agreement does not establish patch support')
    else:require(not r['supported_cycle'][7,20],'isolated pair was not rejected by its missing neighbourhood')


def replay_control():
    audit.assert_replay({'disparity_px':np.array([1.],np.float32)},
                        {'disparity_px':np.array([1.0625],np.float32)})


def self_test()->dict:
    start=time.perf_counter();checks=[];details=io.StringIO()
    def check(name,fn):
        try:fn();checks.append({'name':name,'pass':True});print('[fsg-supported-check] PASS',name)
        except Exception as exc:checks.append({'name':name,'pass':False,'error':repr(exc)});print('[fsg-supported-check] FAIL',name,repr(exc))
    check('frozen sources and candidate code identity',comparison.check_sources)
    check('one update exactly reproduces independent audit stage 1',iteration_control)
    check('three-update negative fails',lambda:raises(AssertionError,lambda:iteration_control(True)))
    check('interpolated cancellation rejected by active endpoints',cycle_control)
    check('endpoint negative fails',lambda:raises(AssertionError,lambda:cycle_control(True)))
    check('perfect isolated cycle rejected by footprint',footprint_control)
    check('footprint negative fails',lambda:raises(AssertionError,lambda:footprint_control(True)))
    check('stale-result negative fails',lambda:raises(ValueError,replay_control))
    st=isolated_state();a=st['disparity_left'].copy();b=st['disparity_right'].copy()
    good=st['valid_left'];ids=st['ids_left'];a[7,20]=10.;b[7,10]=-10.;b[7,11]=np.nan
    othergood=good.copy();othergood[7,11]=False
    ep=f.endpoint_cycle(a,b,good,othergood,ids,ids)
    check('zero-weight invalid neighbour is ignored',lambda:require(ep['ok'][7,20] and ep['weight1'][7,20]==0))
    a[7,20]=9.999
    ep=f.endpoint_cycle(a,b,good,othergood,ids,ids)
    check('tiny positive-weight invalid contributor is not ignored',lambda:require(not ep['ok'][7,20]))
    st=isolated_state();st['disparity_left'][:]=10.;st['disparity_right'][:]=-10.
    r=f.supported_cycles(st)
    check('coherent reciprocal field retains interior',lambda:require(r['supported_cycle'][5:10,15:25].all()))
    # The same test illustrates a limitation: without sensory/ground-truth
    # evidence this constant field could have the wrong depth and still pass.
    check('coherent but hypothetically wrong fields are NOT certified safe',lambda:require(r['supported_cycle'][7,20]))
    check('out-of-image correspondences are rejected',lambda:require(not r['endpoint_left'][:,:10].any()))
    negative_ids=ids.copy();negative_ids[:,10]=2
    bad=f.endpoint_cycle(st['disparity_left'],st['disparity_right'],good,good,ids,negative_ids)
    check('different endpoint object ID rejected',lambda:require(not bad['ok'][7,20]))
    mask=np.zeros((11,11),bool);mask[3:8,3:8]=True
    eroded=f.footprint_support(mask)
    check('full 5x5 footprint retains exactly its centre',lambda:require(eroded.sum()==1 and eroded[5,5]))
    check('footprint border is zero not reflected',lambda:require(not f.footprint_support(np.ones((7,7),bool))[0].any()))
    flat=np.ones((30,40,3),np.float32);d=np.full((30,40),4.2,np.float32)
    check('flat refinement leaves disparity unchanged',lambda:require(np.array_equal(f.refine_once(flat,flat,d,np.ones_like(d,bool)),d)))
    rng=np.random.default_rng(992);l=rng.random(flat.shape,dtype=np.float32);rr=rng.random(flat.shape,dtype=np.float32)
    supported=rng.random(d.shape)>.3;once=f.refine_once(l,rr,d,supported)
    check('one update never moves beyond 0.5 pixels',lambda:require(np.max(np.abs(once-d))<=.500001))
    check('unsupported values remain unchanged',lambda:require(np.array_equal(once[~supported],d[~supported])))
    with tempfile.TemporaryDirectory(prefix='fsg1f-check-') as t:
        root=Path(t);run=root/'small31';pred=root/'old'
        with contextlib.redirect_stdout(details):fixtures.make_synthetic(run);validation.infer_pair(run/'step_right',pred)
        folder=run/'step_right';c,obs=hdr.read_observation(folder)
        original={k:v.copy() for k,v in obs.items()}
        old,_=hdr.compute_candidate(c,obs)
        records,meta,fields=f.compute_variants(c,obs)
        after,_=hdr.compute_candidate(c,obs)
        check('legacy HDR result is unchanged by new computation',lambda:audit.assert_replay(old,after))
        check('observation arrays were not mutated',lambda:require(all(np.array_equal(obs[k],v) for k,v in original.items())))
        check('one-step control freshly recomputes its validity',lambda:require(meta['one_step_control']['matcher']['refinement_iterations']==1))
        check('all three variants share one-step disparities',lambda:require(all(np.array_equal(r['disparity_px'],records['one_step_control']['disparity_px']) for r in records.values())))
        check('endpoint and candidate supports are nested',lambda:require(not np.any(records['candidate']['valid']&~records['endpoint_control']['valid']) and not np.any(records['endpoint_control']['valid']&~records['one_step_control']['valid'])))
        check('missing points remain NaN in every variant',lambda:require(all(np.isnan(r['xyz_h'][~r['valid']]).all() for r in records.values())))
        check('candidate output is not empty in the calibration fixture',lambda:require(records['candidate']['valid'].any()))
        check('metadata does not certify visibility or adopt a default',lambda:require(all(not m['visibility_is_certified'] and not m['adopted_default'] for m in meta.values())))
        check('truth-shaped inputs are forbidden',lambda:raises(ValueError,lambda:f.compute_variants(c,{**obs,'truth':np.zeros((1,))})))
        unchanged=paired.snapshot([run,pred])
        with contextlib.redirect_stdout(details):report=comparison.compare_pair(folder,{'legacy':pred/'stereo_legacy','hdr':pred/'stereo_candidate'},root/'comparison',True,True)
        check('both frozen estimators replayed exactly',lambda:require(report['exact_legacy_and_hdr_replay']))
        check('comparison preserves all input bytes',lambda:require(paired.snapshot([run,pred])==unchanged))
        check('identical fixed reference masks used by all instruments',lambda:require(report['same_fixed_references']))
        check('new predictions saved before ground truth',lambda:require(report['predictions_saved_before_truth']))
        check('each variant has its own recomputed metrics',lambda:require(all(k in report['instruments'] for k in f.VARIANTS)))
        mesh=audit.load_npz(folder/'evaluation_only'/'mesh.npz')
        def independent_reference_check():
            for name,record in records.items():
                independent,ctx=paired.candidate_evaluation(c,record,mesh,False,True)
                reused=comparison.evaluate_on_context(record,ctx,False,True)
                for key in ('metrics','fails','checks_pass','wrong_instance_accepted_count','reference_status'):
                    require(reused[key]==independent[key],'reused reference changed evaluation: '+key)
        check('reference reuse equals independent evaluator for all variants',independent_reference_check)
        check('comparison visuals and occlusion CSV exist',lambda:require((root/'comparison'/'supported_comparison.png').exists() and (root/'comparison'/'occlusion_tracking.csv').exists()))
        check('candidate and ablations are not auto-promoted',lambda:require(not report['full_profile_milestone_pass'] and not report['fusion_authorized'] and report['controls_are_not_automatic_fallbacks']))
        check('overwrite refused',lambda:raises(ValueError,lambda:comparison.compare_pair(folder,{'legacy':pred/'stereo_legacy','hdr':pred/'stereo_candidate'},root/'comparison',True,True)))
        check('synthetic records rejected in real mode',lambda:raises(ValueError,lambda:comparison.compare_pair(folder,{'legacy':pred/'stereo_legacy','hdr':pred/'stereo_candidate'},root/'no-real',True,False)))
        truth=folder/'evaluation_only';hidden=root/'hidden_truth';truth.rename(hidden)
        try:
            counts=f.reconstruct_pair(folder,root/'no_truth_inference')
            check('inference works with evaluator geometry absent',lambda:require(counts['candidate']==int(records['candidate']['valid'].sum())))
            stored=audit.load_npz(root/'no_truth_inference'/'candidate'/'result.npz')
            check('truth removal changes no reconstructed array',lambda:audit.assert_replay(records['candidate'],stored))
        finally:hidden.rename(truth)
        check('inference refuses source-overlapping output',lambda:raises(ValueError,lambda:f.reconstruct_pair(folder,folder/'output')))
        zero={**obs,'rgb_L':np.zeros_like(obs['rgb_L']),'rgb_R':np.zeros_like(obs['rgb_R'])}
        z,_,_=f.compute_variants(c,zero)
        check('blank images do not produce accepted geometry',lambda:require(not any(v['valid'].any() for v in z.values())))
        metric=report['instruments']['candidate']['evaluation'];fake={'checks_pass':False,'accepted_core':1}
        check('one unsafe core pixel still fails the preserved safety rule',lambda:require(any('limit=0' in x for x in comparison.combined_gates(metric,fake))))
        broken=audit.load_npz(pred/'stereo_candidate'/'result.npz');broken['disparity_px'][0,0]+=.125
        check('stored disparity change fails exact replay',lambda:raises(ValueError,lambda:audit.assert_replay(old,broken)))
        check('all metadata and numeric reports are strict JSON',lambda:json.dumps(report,allow_nan=False))
        check('after negative tests original inputs still identical',lambda:require(paired.snapshot([run,pred])==unchanged))
    passed=sum(x['pass'] for x in checks)
    result={'passed':passed,'failed':len(checks)-passed,'seconds':time.perf_counter()-start,'checks':checks,
            'blender_executed':False,'detail_log':details.getvalue(),
            'note':'Software correctness checks, not validation on Code\'s Cycles observations.'}
    print(f"[fsg-supported-check] SUMMARY passed={passed} failed={result['failed']} seconds={result['seconds']:.3f} blender_executed=False")
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__);mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--self-test',action='store_true');mode.add_argument('--negative',choices=('iterations','cycle','footprint','replay'))
    ap.add_argument('--report',type=Path);args=ap.parse_args()
    if args.negative:
        {'iterations':lambda:iteration_control(True),'cycle':lambda:cycle_control(True),
         'footprint':lambda:footprint_control(True),'replay':replay_control}[args.negative]()
        raise AssertionError('negative unexpectedly passed')
    result=self_test()
    if args.report:g.json_write(args.report,result)
    raise SystemExit(0 if not result['failed'] else 1)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print(f'[fsg-supported-check] FAIL {type(exc).__name__}: {exc}',file=sys.stderr);raise SystemExit(1)
