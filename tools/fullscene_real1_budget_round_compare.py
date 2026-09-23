from __future__ import annotations
import argparse,json
from pathlib import Path
import fullscene_real1_budget_round_public as public
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('out',type=Path); a=ap.parse_args(); m=json.loads((a.out/'budget_round_manifest.json').read_text()); f=[]
 if m.get('schema')!=public.SPEC_ID:f.append('schema')
 if not m.get('one_round_complete'):f.append('one_round')
 if int(m.get('round_fixation_limit_per_target',-1))!=6:f.append('round_limit')
 if int(m.get('handoff_actions',-1))!=0:f.append('handoff')
 if m.get('truth_opened_before_seal') is not False:f.append('truth_barrier')
 for t in m.get('targets',[]):
  n=int(t.get('continuation',{}).get('fresh_fixation_count',-1))
  if n<0 or n>6:f.append('fresh_count')
 print('FULLSCENE_REAL1_BUDGET_ROUND_COMPLETE structural_fails:',f); raise SystemExit(1 if f else 0)
if __name__=='__main__':main()
