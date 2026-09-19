"""Fail-capable software checks for FSG4 Increment 4 / FSG4b pairing orchestration."""
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
import fsg4_public as public
import fsg4_scene as scene
import fsg4_policy as policy
import fsg4_metrics as metrics
import fsg4_pair


def _write_fake_acquisition(root: Path, step: int = 2, yaw: float = -10.0) -> Path:
    acq_root=root/f"fix_{step:02d}";case=acq_root/f"fix_{step:02d}";ev=case/"evaluation_only"
    ev.mkdir(parents=True)
    rgb=np.arange(24,dtype=np.float32).reshape(2,4,3)/17.0
    ids=np.full((2,4),public.OBJECT_ID,np.int32)
    np.savez_compressed(case/"observation.npz",rgb_L=rgb,rgb_R=rgb+0.25,instance_L=ids,instance_R=ids)
    (case/"calibration.json").write_text('{}')
    np.savez_compressed(ev/"mesh.npz",dummy=np.array([1,2,3],np.int32))
    seeds=[public.render_seed('case_a',401,yaw,0),public.render_seed('case_a',401,yaw,1)]
    acq={"schema":"test","case":f"fix_{step:02d}","step":step,"fixture":"case_a","profile":"small",
         "yaw_deg":yaw,"seeds_lr":seeds,"primary_camera_samples":1234,"render_seconds_lr":[.1,.1]}
    (case/"acquisition.json").write_text(json.dumps(acq))
    run={"schema":"test","complete":True,"case":f"fix_{step:02d}","step":step,"fixture":"case_a",
         "profile":"small","seed":401,"yaw_deg":yaw,"seeds_lr":seeds,"primary_camera_samples":1234,
         "public_spec_sha256":public.public_digest(),"truth_spec_sha256":"synthetic","total_wall_seconds":.2}
    (acq_root/"run.json").write_text(json.dumps(run))
    return acq_root


def run()->int:
    passed=failed=0
    tests=[]
    tests.append(("scene self test",scene.self_test))
    tests.append(("policy self test",policy.self_test))
    def paired_seed_contract():
        a=public.render_seed('case_a',401,-5,0)
        b=public.render_seed('case_a',401,-5,0)
        c=public.render_seed('case_a',401,-5,1)
        assert a==b and a!=c
        params=tuple(inspect.signature(public.render_seed).parameters)
        assert 'step' not in params and 'policy' not in params and 'policy_name' not in params
    tests.append(("paired yaw-keyed render seeds",paired_seed_contract))
    def exact_reuse_contract():
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);active=td/'active';scan=td/'scan';
            src=_write_fake_acquisition(active/'acquisitions')
            args=SimpleNamespace(fixture='case_a',profile='small',seed=401)
            case,run=fsg4_pair.clone_paired_view(src,args,3,-10.0,scan/'acquisitions')
            src_obs=src/'fix_02'/'observation.npz';dst_obs=case/'observation.npz'
            assert src_obs.read_bytes()==dst_obs.read_bytes(), 'reused observation bytes changed'
            assert run['paired_observation_reused'] and run['new_primary_camera_samples']==0
            assert run['primary_camera_samples']==1234 and run['step']==3 and run['case']=='fix_03'
            ma={"fixation_yaws_deg":[-10.0]};ms={"fixation_yaws_deg":[-10.0]}
            # Re-home to the exact layout expected by verify_shared_views.
            ar=td/'ar';sr=td/'sr'
            (ar/'acquisitions').mkdir(parents=True);(sr/'acquisitions').mkdir(parents=True)
            import shutil
            shutil.copytree(src,ar/'acquisitions'/'fix_00')
            # rename source case and metadata to fix_00 for the verifier
            (ar/'acquisitions'/'fix_00'/'fix_02').rename(ar/'acquisitions'/'fix_00'/'fix_00')
            ac=json.loads((ar/'acquisitions'/'fix_00'/'fix_00'/'acquisition.json').read_text());ac['case']='fix_00';ac['step']=0
            (ar/'acquisitions'/'fix_00'/'fix_00'/'acquisition.json').write_text(json.dumps(ac))
            shutil.copytree(scan/'acquisitions'/'fix_03',sr/'acquisitions'/'fix_00')
            (sr/'acquisitions'/'fix_00'/'fix_03').rename(sr/'acquisitions'/'fix_00'/'fix_00')
            ac=json.loads((sr/'acquisitions'/'fix_00'/'fix_00'/'acquisition.json').read_text());ac['case']='fix_00';ac['step']=0
            (sr/'acquisitions'/'fix_00'/'fix_00'/'acquisition.json').write_text(json.dumps(ac))
            paired=fsg4_pair.verify_shared_views(ar,sr,ma,ms)
            assert paired['all_exact'] and paired['all_scan_shared_views_reused']
    tests.append(("exact shared-view artifact reuse",exact_reuse_contract))
    def fixed_scan_contract():
        assert tuple(public.SCAN_YAWS_DEG)==(0.0,-5.0,5.0,-10.0,10.0)
        assert len(set(public.SCAN_YAWS_DEG))==public.MAX_BUDGET_FIXATIONS
        src=(Path(__file__).resolve().parents[1]/'fsg4_run.py').read_text()
        assert 'import fsg4_scene' not in src and 'evaluation_only' not in src
        assert 'view_provider' in src
    tests.append(("fixed scan and truth-free host",fixed_scan_contract))
    def auc_contract():
        active=[.40,.60,.80,.98,1.0];scan=[.40,.40,.60,.60,.80]
        ga=metrics.normalized_auc(active)-metrics.normalized_auc(scan)
        assert ga>.10
        assert metrics.pad_curve([.4,.7,.95],5)==[.4,.7,.95,.95,.95]
    tests.append(("paired AUC metric",auc_contract))
    def public_contract():
        assert public.PUBLIC_SPEC['fixed_head_frame'] and public.PUBLIC_SPEC['paired_render_noise_by_fixture_seed_yaw']
        assert set(public.FIXTURES)=={'case_a','case_b'} and set(public.SEEDS)=={401,443}
    tests.append(("public comparison contract",public_contract))
    for name,fn in tests:
        try:fn();print('[fsg4-check] PASS',name);passed+=1
        except Exception as e:print('[fsg4-check] FAIL',name,type(e).__name__,e);failed+=1
    print(f'[fsg4-check] SUMMARY passed={passed} failed={failed}')
    return failed


def negative(kind:str)->None:
    if kind=='frontier':
        n=128;sup=np.ones((n,n),bool);ids=np.full((n,n),public.OBJECT_ID,np.int32);ids[:,:12]=public.BACKGROUND_ID
        yaw=np.radians(np.linspace(-4,6,1500));xyz=np.c_[2*np.sin(yaw),np.zeros_like(yaw),-2*np.cos(yaw)]
        d=policy.choose_next(0,{'nominal_core_fov_deg':12.0},ids,sup,xyz,[0])
        assert d['next_yaw_deg']==-5.0,'deliberate hard-coded/wrong frontier direction detected'
    elif kind=='scan':
        bad=(0.0,-5.0,-10.0,-15.0,-20.0)
        assert tuple(public.SCAN_YAWS_DEG)==bad,'deliberate fixture-favouring scan mutation detected'
    elif kind=='pairing':
        # The repaired contract is still exact: even a one-float mutation must fail.
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);ar=td/'active';sr=td/'scan';
            src=_write_fake_acquisition(ar/'acquisitions',0,-10.0)
            import shutil
            shutil.copytree(src,sr/'acquisitions'/'fix_00')
            case=sr/'acquisitions'/'fix_00'/'fix_00'
            ac=json.loads((case/'acquisition.json').read_text());ac['paired_observation_reused']=True
            (case/'acquisition.json').write_text(json.dumps(ac))
            with np.load(case/'observation.npz',allow_pickle=False) as f:obs={k:f[k] for k in f.files}
            obs['rgb_L']=obs['rgb_L'].copy();obs['rgb_L'].flat[0]+=np.float32(1e-4)
            np.savez_compressed(case/'observation.npz',**obs)
            fsg4_pair.verify_shared_views(ar,sr,{"fixation_yaws_deg":[-10.0]},{"fixation_yaws_deg":[-10.0]})
        raise AssertionError('deliberate paired-observation mutation was not detected')
    elif kind=='auc':
        active=[.4,.45,.50,.55,.60];scan=[.4,.55,.65,.75,.80]
        gain=metrics.normalized_auc(active)-metrics.normalized_auc(scan)
        assert gain>=public.TARGETS['mean_auc_gain_min'],'deliberate no-active-advantage curve detected'
    else:raise ValueError(kind)


def main()->None:
    ap=argparse.ArgumentParser();ap.add_argument('--self-test',action='store_true');ap.add_argument('--negative',choices=('frontier','scan','pairing','auc'));a=ap.parse_args()
    if a.negative:
        try:negative(a.negative)
        except Exception as e:print('[fsg4-check] FAIL',type(e).__name__,e);raise SystemExit(1)
        raise SystemExit(0)
    raise SystemExit(run())

if __name__=='__main__':main()
