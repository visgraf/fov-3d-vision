"""Public contract: one extra quarter-budget continuation round after REAL-1."""
from __future__ import annotations
import hashlib, json
SPEC_ID="FullSceneREAL1-watchdog-continuation-one-round-v1"
BASELINE_RESULT_COMMIT="f49ec8e"
RUN_BRANCH="fullscene-real-1"
BASELINE_OUT="previews/fullscene-real1/full-seed2111"
SEED=2111
TARGET_BASELINE_STATUS="WATCHDOG_REACHED_RETAIN_FOR_REVISIT"
ORIGINAL_WATCHDOG_FIXATIONS=24
ROUND_FIXATION_LIMIT=6  # exactly one additional quarter of the original watchdog
PUBLIC_SPEC={
 "id":SPEC_ID,
 "baseline_result_commit":BASELINE_RESULT_COMMIT,
 "run_branch":RUN_BRANCH,
 "baseline_out":BASELINE_OUT,
 "question":"After a 24-fixation engineering watchdog interrupts an object while frozen FSG6f still wants to continue, how much attention/geometric/control progress does exactly one additional quarter-budget round buy?",
 "target_selection":"dynamically select baseline REAL-1 rows with WATCHDOG_REACHED_RETAIN_FOR_REVISIT; no scene object id is hard-coded",
 "one_round":{
   "original_watchdog_fixations":ORIGINAL_WATCHDOG_FIXATIONS,
   "fresh_fixation_limit_per_target":ROUND_FIXATION_LIMIT,
   "rationale":"one additional quarter of the original 24-fixation guardrail; diagnostic block, not a new budget policy",
   "stop_early_only_on_frozen_scientific_stop":True,
   "no_second_block":True,
 },
 "control":"resume each selected object's saved final REAL-1 map/history and use unchanged multiobject2c_policy/FSG6f, generic renderer, 12 mm association, and empty-look semantics",
 "handoff":"disabled for this experiment so budget is the only opened causal variable",
 "audit":"after the one continuation block, run the established read-only epistemic audit; audit does not trigger more actions",
 "truth":"control may not read reference/evaluator products; after a continuation seal, a separate evaluator may compare against the already-generated immutable REAL-1 reference panorama",
 "metrics":"keep geometric growth, spherical coverage, depth error, attention residue, measurement residue, and control state separate; no score and no budget formula is fitted",
 "integrity":[
   "completed REAL-1 baseline artifacts/maps remain read-only",
   "non-target scene objects remain read-only",
   "no re-seeding and no historical rerender",
   "no modification of frozen FSG6f/renderer/stereo/fusion/audit machinery",
   "no adaptive budget scaling inside this experiment",
 ],
}
def public_digest():
 return hashlib.sha256(json.dumps(PUBLIC_SPEC,sort_keys=True,separators=(",",":")).encode()).hexdigest()
