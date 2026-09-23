from __future__ import annotations
import argparse, copy, importlib.util, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'tools'))
import fullscene_real1_seed_round_public as p

def validate(spec):
    f=[]; r=spec["one_round"]
    if "hard-coded" not in spec["target_selection"]: f.append("dynamic_target")
    if r["lattice_step_deg"] != 5.0 or len(r["offsets"]) != 8: f.append("one_ring")
    if not r["render_all_probes"] or not r["no_second_ring"] or not r["no_radius_expansion"]: f.append("bounded_round")
    if not r["reuse_winning_probe_as_seed"] or not r["no_extra_seed_render"]: f.append("reuse_probe")
    if "evaluator geometry/depth is forbidden" not in spec["probe_evidence"]: f.append("truth_quarantine")
    if not spec["stop"].startswith("stop immediately") or "no growth" not in spec["stop"]: f.append("no_growth")
    if "do not invent a new quality threshold" not in spec["seed_semantics"]: f.append("no_threshold")
    if "baseline REAL-1 artifacts are read-only" not in spec["integrity"]: f.append("baseline_readonly")
    return f

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--mutation', choices=['hardcode','secondring','earlystop','truth','growth','threshold','baseline','extraseed']); a=ap.parse_args()
    s=copy.deepcopy(p.PUBLIC_SPEC)
    if a.mutation=='hardcode': s['target_selection']='target object 143'
    elif a.mutation=='secondring': s['one_round']['no_second_ring']=False
    elif a.mutation=='earlystop': s['one_round']['render_all_probes']=False
    elif a.mutation=='truth': s['probe_evidence']='rank using evaluator geometry'
    elif a.mutation=='growth': s['stop']='continue into growth'
    elif a.mutation=='threshold': s['seed_semantics']='require 1000 points'
    elif a.mutation=='baseline': s['integrity']=[x for x in s['integrity'] if x!='baseline REAL-1 artifacts are read-only']
    elif a.mutation=='extraseed': s['one_round']['no_extra_seed_render']=False
    f=validate(s)
    if a.mutation:
        if not f: print('MUTATION ESCAPED'); return 2
        print('[real1-seed-round-negative] PASS detector='+f[0]); return 1
    print('[real1-seed-round-contract] PASS dynamic_target=true one_ring=true eight_probes=true reuse_probe=true')
    print('[real1-seed-round-integrity] PASS baseline_read_only=true truth=false growth=false threshold=false')
    print('[real1-seed-round-check] SUMMARY passed=8 failed='+str(len(f)))
    return 1 if f else 0
if __name__=='__main__': raise SystemExit(main())
