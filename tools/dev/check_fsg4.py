"""Fail-capable software checks for FSG4 Increment 4."""
from __future__ import annotations
import argparse
import inspect
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fsg4_public as public
import fsg4_scene as scene
import fsg4_policy as policy
import fsg4_metrics as metrics


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
        # Seed is yaw-keyed: step/policy do not appear in the function signature or source.
        params=tuple(inspect.signature(public.render_seed).parameters)
        assert 'step' not in params and 'policy' not in params and 'policy_name' not in params
    tests.append(("paired yaw-keyed render seeds",paired_seed_contract))
    def fixed_scan_contract():
        assert tuple(public.SCAN_YAWS_DEG)==(0.0,-5.0,5.0,-10.0,10.0)
        assert len(set(public.SCAN_YAWS_DEG))==public.MAX_BUDGET_FIXATIONS
        src=(Path(__file__).resolve().parents[1]/'fsg4_run.py').read_text()
        assert 'import fsg4_scene' not in src and 'evaluation_only' not in src
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
        y=-5.0
        good=public.render_seed('case_a',401,y,0)
        bad=good+100  # models accidental step-dependent seed drift
        assert good==bad,'deliberate paired-noise mismatch detected'
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
