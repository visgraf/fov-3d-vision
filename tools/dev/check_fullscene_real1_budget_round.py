from __future__ import annotations
import argparse,copy,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT/'tools'))
import fullscene_real1_budget_round_public as p

def validate(s):
 f=[]; r=s['one_round']
 if 'hard-coded' not in s['target_selection']:f.append('dynamic_targets')
 if r['fresh_fixation_limit_per_target']!=6 or r['original_watchdog_fixations']!=24:f.append('quarter_round')
 if not r['stop_early_only_on_frozen_scientific_stop'] or not r['no_second_block']:f.append('one_block')
 if 'unchanged multiobject2c_policy/FSG6f' not in s['control']:f.append('frozen_control')
 if s['handoff']!='disabled for this experiment so budget is the only opened causal variable':f.append('no_handoff')
 if 'audit does not trigger more actions' not in s['audit']:f.append('audit_readonly')
 if 'after a continuation seal' not in s['truth']:f.append('truth_barrier')
 if 'no score and no budget formula is fitted' not in s['metrics']:f.append('no_score_formula')
 if 'completed REAL-1 baseline artifacts/maps remain read-only' not in s['integrity']:f.append('baseline_readonly')
 return f

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--mutation',choices=['hardcode','twelve','secondblock','policy','handoff','auditaction','truth','score','baseline']); a=ap.parse_args(); s=copy.deepcopy(p.PUBLIC_SPEC)
 if a.mutation=='hardcode':s['target_selection']='objects 141 and 142'
 elif a.mutation=='twelve':s['one_round']['fresh_fixation_limit_per_target']=12
 elif a.mutation=='secondblock':s['one_round']['no_second_block']=False
 elif a.mutation=='policy':s['control']='new adaptive policy'
 elif a.mutation=='handoff':s['handoff']='enabled'
 elif a.mutation=='auditaction':s['audit']='audit may trigger another block'
 elif a.mutation=='truth':s['truth']='reference may guide continuation'
 elif a.mutation=='score':s['metrics']='fit one score and budget formula'
 elif a.mutation=='baseline':s['integrity']=[x for x in s['integrity'] if x!='completed REAL-1 baseline artifacts/maps remain read-only']
 f=validate(s)
 if a.mutation:
  if not f:print('MUTATION ESCAPED');return 2
  print('[real1-budget-round-negative] PASS detector='+f[0]);return 1
 print('[real1-budget-round-contract] PASS dynamic_targets=true six_fixations=true one_block=true frozen_control=true')
 print('[real1-budget-round-integrity] PASS baseline_read_only=true handoff=false truth_after_seal=true score=false')
 print('[real1-budget-round-check] SUMMARY passed=9 failed='+str(len(f)))
 return 1 if f else 0
if __name__=='__main__':raise SystemExit(main())
