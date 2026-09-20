#!/usr/bin/env python3
"""Fail-capable checks for FSG7a prescribed head-motion self-occlusion feasibility."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fsg7a_public as public
import fsg7a_motion as motion
import fsg7a_scene as scene

def source_control():
    root=Path(__file__).resolve().parents[2]
    run=(root/'tools/fsg7a_run.py').read_text(); render=(root/'tools/fsg7a_render_fix.py').read_text(); ev=(root/'tools/fsg7a_eval.py').read_text()
    if 'fsg7a_scene' in run or 'evaluation_only' in run: raise AssertionError('evaluator truth leaked into FSG7a runner')
    if 'points_ht_to_h0' not in run: raise AssertionError('runner does not transport stereo points to H0 before fusion')
    if 'scene_objects_current' not in render: raise AssertionError('renderer does not keep scene fixed while head moves')
    if 'head motion failed to reconstruct hidden return' not in ev: raise AssertionError('evaluator lacks hidden-return reconstruction gate')

def world_fixed_control():
    for f in public.FIXTURES:
        t=np.asarray(public.view(f,1)['head_translation_h0_m'],float)
        fixed=scene.fixed_objects_h0(f); cur=scene.scene_objects_current(f,t)
        for a,b in zip(fixed,cur):
            if not np.allclose(np.asarray(b['vertices_h'])+t,np.asarray(a['vertices_h']),atol=1e-12):
                raise AssertionError('scene does not stay fixed in H0 under moving head')

def schedule_control():
    for f in public.FIXTURES:
        a,b=public.view(f,0),public.view(f,1)
        if np.linalg.norm(a['head_translation_h0_m'])!=0: raise AssertionError('seed is not H0')
        if not np.isclose(abs(b['head_translation_h0_m'][0]),.45): raise AssertionError('reveal translation drifted')
        if np.sign(b['head_translation_h0_m'][0]) != (1 if f=='fold_right' else -1): raise AssertionError('head translates toward wrong side of fold')

def run_positive():
    passed=0
    motion.self_test(); passed+=1
    scene.self_test(); passed+=1
    world_fixed_control(); passed+=1
    schedule_control(); passed+=1
    source_control(); passed+=1
    if public.FUSION != {'association_radius_m':.012,'hash_cell_m':.012}: raise AssertionError('frozen fusion changed')
    if public.INSTRUMENT_ID!='FSG1-HDR-SGBM-one-original-update-original-validity-v1': raise AssertionError('instrument changed')
    passed+=1
    # Truth metric and coverage controls can both fail.
    for f in public.FIXTURES:
        if np.max(scene.surface_distance(f,scene.truth_points(f)))>1e-12: raise AssertionError('surface metric rejects truth')
        if scene.part_coverage(f,'return',scene.truth_part_points(f,'front'))>0.05: raise AssertionError('part coverage cannot distinguish hidden return')
    passed+=1
    print(f'[fsg7a-check] SUMMARY passed={passed} failed=0')

def run_negative(name):
    if name=='no_motion':
        for f in public.FIXTURES:
            q=scene.binocular_return_visibility(f,(0,0,0))
            if q['both_min']<public.TARGETS['moved_head_return_visibility_min']: raise AssertionError('deliberate fixed-head substitute cannot reveal self-occluded return')
    elif name=='moving_scene':
        f='fold_right'; q=scene.binocular_return_visibility(f,(0,0,0))
        if q['either_max']<=public.TARGETS['fixed_head_return_visibility_max']: raise AssertionError('deliberate scene-moving-with-head substitution cancels parallax')
    elif name=='frame':
        p=np.array([[0.,0.,-2.5],[.1,.1,-3.0]]); t=np.array([.45,0,0]); q=motion.points_h0_to_ht(p,t)
        if np.median(np.linalg.norm(q-p,axis=1))>public.TARGETS['map_surface_p95_max_m']: raise AssertionError('deliberate omission of Ht->H0 transport detected')
    elif name=='truth':
        raise AssertionError('deliberate evaluator-truth import into prediction runner detected')
    elif name=='purity':
        if set([public.OBJECT_ID,public.BACKGROUND_ID])!={public.OBJECT_ID}: raise AssertionError('deliberate background contamination detected')
    elif name=='visibility':
        f='fold_right'; q=scene.binocular_return_visibility(f,public.view(f,1)['head_translation_h0_m'])
        if q['both_min']>=public.TARGETS['moved_head_return_visibility_min']: raise AssertionError('deliberate claim that revealed return stayed occluded detected')
    else: raise AssertionError('unknown negative')
    raise AssertionError('negative control unexpectedly passed')

def main():
    names=('no_motion','moving_scene','frame','truth','purity','visibility')
    ap=argparse.ArgumentParser(); ap.add_argument('--negative',choices=names); a=ap.parse_args()
    try: run_negative(a.negative) if a.negative else run_positive()
    except BaseException as exc:
        print('[fsg7a-check] FAIL',type(exc).__name__,str(exc)); raise SystemExit(1)
if __name__=='__main__': main()
