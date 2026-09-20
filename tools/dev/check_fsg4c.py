"""Fail-capable checks for the fresh FSG4c efficiency validation."""
from __future__ import annotations
import argparse
import inspect
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fsg4_public as frozen_public
import fsg4_policy as policy
import fsg4_metrics as metrics
import fsg4c_public as public
import fsg4c_scene as scene
import fsg4c_pair


def _write_fake_acquisition(root:Path,step:int=2,yaw:float=-10.0,fixture:str='case_c',seed:int=503)->Path:
    acq_root=root/f'fix_{step:02d}';case=acq_root/f'fix_{step:02d}';ev=case/'evaluation_only';ev.mkdir(parents=True)
    rgb=np.arange(24,dtype=np.float32).reshape(2,4,3)/17.0;ids=np.full((2,4),public.OBJECT_ID,np.int32)
    np.savez_compressed(case/'observation.npz',rgb_L=rgb,rgb_R=rgb+.25,instance_L=ids,instance_R=ids)
    (case/'calibration.json').write_text('{}');np.savez_compressed(ev/'mesh.npz',dummy=np.array([1,2,3],np.int32))
    seeds=[public.render_seed(fixture,seed,yaw,0),public.render_seed(fixture,seed,yaw,1)]
    acq={'schema':'test','case':f'fix_{step:02d}','step':step,'fixture':fixture,'profile':'small','yaw_deg':yaw,'seeds_lr':seeds,'primary_camera_samples':1234,'render_seconds_lr':[.1,.1]}
    (case/'acquisition.json').write_text(json.dumps(acq))
    run={'schema':'test','complete':True,'case':f'fix_{step:02d}','step':step,'fixture':fixture,'profile':'small','seed':seed,'yaw_deg':yaw,'seeds_lr':seeds,'primary_camera_samples':1234,'public_spec_sha256':public.public_digest(),'truth_spec_sha256':'synthetic','total_wall_seconds':.2}
    (acq_root/'run.json').write_text(json.dumps(run));return acq_root


def run()->int:
    passed=failed=0;tests=[]
    tests.append(('fresh scene design',scene.self_test))
    def frozen_policy_contract():
        assert public.POLICY==frozen_public.POLICY
        assert public.OBJECT_ID==frozen_public.OBJECT_ID and public.BACKGROUND_ID==frozen_public.BACKGROUND_ID
        assert tuple(public.SCAN_YAWS_DEG)==tuple(frozen_public.SCAN_YAWS_DEG)==(0.0,-5.0,5.0,-10.0,10.0)
        src=(Path(__file__).resolve().parents[1]/'fsg4c_run.py').read_text()
        assert 'import fsg4_policy as policy' in src and 'import fsg4c_scene' not in src and 'evaluation_only' not in src
    tests.append(('frozen policy and scan',frozen_policy_contract))
    def fresh_schedule_contract():
        assert set(public.FIXTURES)=={'case_c','case_d'} and set(public.SEEDS)=={503,557}
        assert set(public.FIXTURES).isdisjoint(set(frozen_public.FIXTURES)) and set(public.SEEDS).isdisjoint(set(frozen_public.SEEDS))
        params=tuple(inspect.signature(public.render_seed).parameters);assert 'step' not in params and 'policy' not in params
    tests.append(('fresh fixtures seeds and yaw-keyed noise',fresh_schedule_contract))
    def exact_reuse_contract():
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);active=td/'active';scan=td/'scan';src=_write_fake_acquisition(active/'acquisitions')
            args=SimpleNamespace(fixture='case_c',profile='small',seed=503)
            case,rr=fsg4c_pair.clone_paired_view(src,args,3,-10.0,scan/'acquisitions')
            assert (src/'fix_02'/'observation.npz').read_bytes()==(case/'observation.npz').read_bytes()
            assert rr['paired_observation_reused'] and rr['new_primary_camera_samples']==0 and rr['primary_camera_samples']==1234
            ar=td/'ar';sr=td/'sr';(ar/'acquisitions').mkdir(parents=True);(sr/'acquisitions').mkdir(parents=True)
            import shutil
            shutil.copytree(src,ar/'acquisitions'/'fix_00');(ar/'acquisitions'/'fix_00'/'fix_02').rename(ar/'acquisitions'/'fix_00'/'fix_00')
            ac=json.loads((ar/'acquisitions'/'fix_00'/'fix_00'/'acquisition.json').read_text());ac['case']='fix_00';ac['step']=0;(ar/'acquisitions'/'fix_00'/'fix_00'/'acquisition.json').write_text(json.dumps(ac))
            shutil.copytree(scan/'acquisitions'/'fix_03',sr/'acquisitions'/'fix_00');(sr/'acquisitions'/'fix_00'/'fix_03').rename(sr/'acquisitions'/'fix_00'/'fix_00')
            ac=json.loads((sr/'acquisitions'/'fix_00'/'fix_00'/'acquisition.json').read_text());ac['case']='fix_00';ac['step']=0;(sr/'acquisitions'/'fix_00'/'fix_00'/'acquisition.json').write_text(json.dumps(ac))
            paired=fsg4c_pair.verify_shared_views(ar,sr,{'fixation_yaws_deg':[-10.0]},{'fixation_yaws_deg':[-10.0]})
            assert paired['all_exact'] and paired['all_scan_shared_views_reused']
    tests.append(('exact shared-view artifact reuse',exact_reuse_contract))
    def efficiency_contract():
        active=[.40,.60,.80,.98,1.0];scan=[.40,.40,.60,.60,.80]
        assert metrics.normalized_auc(active)-metrics.normalized_auc(scan)>.10
        assert metrics.pad_curve([.4,.7,.95],5)==[.4,.7,.95,.95,.95]
    tests.append(('AUC and early-stop budget arithmetic',efficiency_contract))
    def no_novelty_gate_contract():
        assert public.PUBLIC_SPEC['per_fixation_novelty_and_gain_are_descriptive_only'] is True
        assert 'minimum_new_fraction_terminal' not in public.TARGETS and 'minimum_incremental_coverage_gain_terminal' not in public.TARGETS
        src=(Path(__file__).resolve().parents[1]/'fsg4c_eval.py').read_text()
        assert "too little new surface" not in src and "added too little visible surface" not in src
        assert 'residual_closure_fraction_by_fixation' in src
    tests.append(('per-fixation novelty is descriptive only',no_novelty_gate_contract))
    def policy_state_contract():
        n=128;sup=np.ones((n,n),bool);ids=np.full((n,n),public.OBJECT_ID,np.int32);ids[:,:12]=public.BACKGROUND_ID
        yaw=np.radians(np.linspace(-4,6,1500));xyz=np.c_[2*np.sin(yaw),np.zeros_like(yaw),-2*np.cos(yaw)]
        d=policy.choose_next(0,{'nominal_core_fov_deg':12.0},ids,sup,xyz,[0]);assert d['next_yaw_deg']==5.0
        ids2=np.full((n,n),public.OBJECT_ID,np.int32);ids2[:,-12:]=public.BACKGROUND_ID
        yaw2=np.radians(np.linspace(-6,4,1500));xyz2=np.c_[2*np.sin(yaw2),np.zeros_like(yaw2),-2*np.cos(yaw2)]
        d2=policy.choose_next(0,{'nominal_core_fov_deg':12.0},ids2,sup,xyz2,[0]);assert d2['next_yaw_deg']==-5.0
    tests.append(('frozen policy responds to map/mask state',policy_state_contract))
    for name,fn in tests:
        try:fn();print('[fsg4c-check] PASS',name);passed+=1
        except Exception as e:print('[fsg4c-check] FAIL',name,type(e).__name__,e);failed+=1
    print(f'[fsg4c-check] SUMMARY passed={passed} failed={failed}');return failed


def negative(kind:str)->None:
    if kind=='frontier':
        n=128;sup=np.ones((n,n),bool);ids=np.full((n,n),public.OBJECT_ID,np.int32);ids[:,:12]=public.BACKGROUND_ID
        yaw=np.radians(np.linspace(-4,6,1500));xyz=np.c_[2*np.sin(yaw),np.zeros_like(yaw),-2*np.cos(yaw)]
        d=policy.choose_next(0,{'nominal_core_fov_deg':12.0},ids,sup,xyz,[0]);assert d['next_yaw_deg']==-5.0,'deliberate hard-coded/wrong frontier direction detected'
    elif kind=='scan':
        bad=(0.0,-5.0,-10.0,-15.0,-20.0);assert tuple(public.SCAN_YAWS_DEG)==bad,'deliberate fixture-favouring scan mutation detected'
    elif kind=='pairing':
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);ar=td/'active';sr=td/'scan';src=_write_fake_acquisition(ar/'acquisitions',0,-10.0);import shutil
            shutil.copytree(src,sr/'acquisitions'/'fix_00');case=sr/'acquisitions'/'fix_00'/'fix_00';ac=json.loads((case/'acquisition.json').read_text());ac['paired_observation_reused']=True;(case/'acquisition.json').write_text(json.dumps(ac))
            with np.load(case/'observation.npz',allow_pickle=False) as f:obs={k:f[k] for k in f.files}
            obs['rgb_L']=obs['rgb_L'].copy();obs['rgb_L'].flat[0]+=np.float32(1e-4);np.savez_compressed(case/'observation.npz',**obs)
            fsg4c_pair.verify_shared_views(ar,sr,{'fixation_yaws_deg':[-10.0]},{'fixation_yaws_deg':[-10.0]})
        raise AssertionError('deliberate paired-observation mutation was not detected')
    elif kind=='auc':
        active=[.4,.45,.50,.55,.60];scan=[.4,.55,.65,.75,.80];gain=metrics.normalized_auc(active)-metrics.normalized_auc(scan)
        assert gain>=public.TARGETS['mean_auc_gain_min'],'deliberate no-active-advantage curve detected'
    elif kind=='novelty':
        # FSG4c must NOT reject a terminal step merely because only 1% remains.
        before=.989;after=1.0;gain=after-before;closure=gain/(1-before)
        assert gain>=.02,'deliberate obsolete per-fixation gain gate detected; residual closure would be 100%'
        assert closure<.99,'deliberate closure arithmetic mutation'
    else:raise ValueError(kind)


def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--self-test',action='store_true');ap.add_argument('--negative',choices=('frontier','scan','pairing','auc','novelty'));a=ap.parse_args()
    if a.negative:
        try:negative(a.negative)
        except Exception as e:print('[fsg4c-check] FAIL',type(e).__name__,e);raise SystemExit(1)
        raise SystemExit(0)
    raise SystemExit(run())

if __name__=='__main__':main()
