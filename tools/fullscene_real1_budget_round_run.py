"""Run exactly one six-fixation continuation block for every REAL-1 watchdog object."""
from __future__ import annotations
import argparse,json,subprocess,time
from pathlib import Path
from typing import Any
import fullscene_real1_budget_round_public as public
from fullscene_real1_budget_round_repo import BudgetRoundRepository

def _w(p:Path,o:Any): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(o,indent=2,sort_keys=True)+"\n")
def _git(repo:Path,*args:str)->str: return subprocess.check_output(["git",*args],cwd=repo,text=True).strip()
def main():
 ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--repo',type=Path,default=Path.cwd()); ap.add_argument('--baseline',type=Path,default=Path(public.BASELINE_OUT)); ap.add_argument('--out',type=Path,required=True); ap.add_argument('--seed',type=int,default=public.SEED); a=ap.parse_args()
 repo=a.repo.resolve(); baseline=(repo/a.baseline).resolve() if not a.baseline.is_absolute() else a.baseline.resolve(); out=a.out.resolve()
 if _git(repo,'branch','--show-current')!=public.RUN_BRANCH: raise RuntimeError('wrong branch')
 if _git(repo,'status','--porcelain'): raise RuntimeError('working tree must be clean')
 if subprocess.call(['git','merge-base','--is-ancestor',public.BASELINE_RESULT_COMMIT,'HEAD'],cwd=repo)!=0: raise RuntimeError('HEAD does not descend from REAL-1 result baseline')
 out.mkdir(parents=True,exist_ok=False); rr=BudgetRoundRepository(repo,baseline,out,a.seed); base=rr.load_baseline()
 rows=[r for r in base['object_rows'] if r.get('status')==public.TARGET_BASELINE_STATUS]
 if not rows: raise RuntimeError('baseline has no watchdog-retained object')
 next_step=int(max(base['fixation_steps']))+1; results=[]
 for row in rows:
  oid=int(row['object_id']); od=out/f'object_{oid}'; od.mkdir(parents=True)
  cont=rr.replay_and_continue(row,public.ROUND_FIXATION_LIMIT,next_step,od)
  fresh=int(cont.get('fresh_fixation_count',0))
  if fresh<0 or fresh>public.ROUND_FIXATION_LIMIT: raise AssertionError('continuation exceeded one-round budget')
  next_step+=fresh
  audit=rr.audit_after_round(row,cont,od)
  results.append({'object_id':oid,'baseline_status':row.get('status'),'continuation':cont,'audit':audit})
 # The baseline is input, not workspace: re-hash every pinned artifact and map
 # before the seal is written.
 baseline_proof=rr.verify_baseline_unchanged()
 seal={'schema':public.SPEC_ID,'public_spec_sha256':public.public_digest(),'baseline_result_commit':public.BASELINE_RESULT_COMMIT,'one_round_complete':True,'round_fixation_limit_per_target':public.ROUND_FIXATION_LIMIT,'handoff_actions':0,'truth_opened_before_seal':False,'returned_handoff_actions':0,'second_block':False,'adaptive_budget_rule_used':False,'reseeded':False,'historical_rerenders':0,'baseline_seal_sha256':base['baseline_seal_sha256'],'baseline_read_only_verified':True,**baseline_proof,'blender_launches':int(rr.blender_launches),'render_seconds':float(rr.render_seconds),'targets':results,'sealed_unix':time.time()}
 # One render per fresh fixation and nothing else, counted rather than asserted.
 _fresh=sum(int(x['continuation'].get('fresh_fixation_count',0)) for x in results)
 if int(rr.blender_launches)!=_fresh: raise AssertionError(f'render count {rr.blender_launches} != fresh fixation count {_fresh}')
 _w(out/'continuation_seal.json',seal); _w(out/'continuation_report.json',seal)
 evaluation=rr.evaluate_after_seal(results,out/'continuation_seal.json',out/'evaluation')
 manifest=dict(seal); manifest['postseal_evaluation']=evaluation; manifest['truth_opened_after_seal']=True
 _w(out/'budget_round_manifest.json',manifest)
 print('[real1-budget-round] COMPLETE '+json.dumps({'targets':len(results),'fresh_fixations':sum(int(x['continuation'].get('fresh_fixation_count',0)) for x in results)}))
if __name__=='__main__': main()
