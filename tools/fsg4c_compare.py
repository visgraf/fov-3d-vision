"""Aggregate the four prospectively fixed fresh FSG4c paired full trials."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import cv2
import fsg4c_public as public
from fsg_geometry import json_write

EXPECTED={(f,s) for f in public.FIXTURES for s in public.SEEDS}


def write_visual(path:Path,rows:list[dict])->None:
    W,H=720,190*len(rows);canvas=np.full((H,W,3),245,np.uint8)
    for j,r in enumerate(rows):
        y0=j*190;cv2.putText(canvas,f"{r['fixture']} seed {r['seed']}",(20,y0+22),cv2.FONT_HERSHEY_SIMPLEX,.55,(20,20,20),1,cv2.LINE_AA)
        cv2.rectangle(canvas,(55,y0+42),(685,y0+160),(210,210,210),1)
        for k in range(6):
            x=55+k*(630//5);cv2.line(canvas,(x,y0+42),(x,y0+160),(230,230,230),1)
        for q in (0,.25,.5,.75,1):
            y=int(y0+160-q*118);cv2.line(canvas,(55,y),(685,y),(232,232,232),1)
        def pts(c):return [(55+i*(630//4),int(y0+160-float(v)*118)) for i,v in enumerate(c)]
        pa=pts(r['active_coverage_by_budget']);ps=pts(r['scan_coverage_by_budget'])
        for p,q in zip(pa[:-1],pa[1:]):cv2.line(canvas,p,q,(30,30,30),2)
        for p,q in zip(ps[:-1],ps[1:]):cv2.line(canvas,p,q,(130,130,130),2)
        for p in pa:cv2.circle(canvas,p,3,(30,30,30),-1)
        for p in ps:cv2.circle(canvas,p,3,(130,130,130),-1)
        cv2.putText(canvas,f"AUC gain {100*r['auc_gain']:.1f} pp; final +{100*r['final_coverage_gain']:.1f} pp",(55,y0+182),cv2.FONT_HERSHEY_SIMPLEX,.45,(20,20,20),1,cv2.LINE_AA)
    cv2.imwrite(str(path),canvas)


def compare(pair_roots:list[Path],out:Path)->dict:
    out=out.resolve()
    if out.exists():raise FileExistsError('comparison output must be new')
    rows=[];seen=set()
    for p in pair_roots:
        r=json.loads((p.resolve()/'pair.json').read_text());key=(r['fixture'],int(r['seed']))
        if key in seen:raise ValueError('duplicate FSG4c pair')
        seen.add(key);rows.append(r)
    if seen!=EXPECTED:raise ValueError(f'FSG4c full pair set incomplete: got {sorted(seen)} expected {sorted(EXPECTED)}')
    rows.sort(key=lambda r:(r['fixture'],r['seed']));t=public.TARGETS;fails=[]
    for r in rows:
        if r['profile']!='full':fails.append(f"{r['fixture']}/{r['seed']} is not full profile")
        if r['active_fails']:fails.append(f"{r['fixture']}/{r['seed']} active run failed")
        if r['scan_fails']:fails.append(f"{r['fixture']}/{r['seed']} scan integrity/accuracy failed")
        if not r['paired_observation_identity'].get('all_exact'):fails.append(f"{r['fixture']}/{r['seed']} paired shared views differ")
        if not r['paired_observation_identity'].get('all_scan_shared_views_reused'):fails.append(f"{r['fixture']}/{r['seed']} shared scan views not declared reused")
        if r['active_primary_camera_samples']>r['scan_primary_camera_samples']:fails.append(f"{r['fixture']}/{r['seed']} active exceeded scan camera budget")
    gains=np.array([r['auc_gain'] for r in rows],float);finals=np.array([r['final_coverage_gain'] for r in rows],float)
    wins=int((gains>0).sum());mean_auc=float(gains.mean());mean_final=float(finals.mean())
    if wins<t['pair_auc_wins_required']:fails.append('active did not win AUC on every paired trial')
    if mean_auc<t['mean_auc_gain_min']:fails.append('mean active AUC advantage below prospective threshold')
    if mean_final<t['mean_final_coverage_gain_min']:fails.append('mean active final-coverage advantage below prospective threshold')
    result={'schema':'FSG4c-comparison-v1','pairs':rows,'pair_count':len(rows),'pair_auc_wins':wins,'mean_auc_gain':mean_auc,
            'mean_final_coverage_gain':mean_final,'auc_gain_by_pair':{f"{r['fixture']}-seed{r['seed']}":r['auc_gain'] for r in rows},
            'final_coverage_gain_by_pair':{f"{r['fixture']}-seed{r['seed']}":r['final_coverage_gain'] for r in rows},
            'targets':t,'fails':fails,'status':'FSG4C_INCREMENT4_PASS' if not fails else 'FSG4C_INCREMENT4_FAIL',
            'claim_scope':'fresh paired efficiency validation on two new opaque planar placements x two fresh Monte-Carlo seeds; not policy optimality or a population estimate'}
    out.mkdir(parents=True);json_write(out/'comparison.json',result);write_visual(out/'coverage_vs_budget.png',rows)
    print('[fsg4c-compare] '+result['status'],json.dumps(result,sort_keys=True),flush=True);return result


def main()->None:
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('pairs',nargs='+',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
    r=compare(a.pairs,a.out);raise SystemExit(0 if not r['fails'] else 2)

if __name__=='__main__':main()
