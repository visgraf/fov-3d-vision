# FSG1e Chat validation record

## Scope

This handoff adds a READ-ONLY audit, not an estimator or a visibility veto. The
actual Cycles observations and saved predictions from Code are not mounted here.
No actual cap population, real leak endpoint pattern, or workstation runtime is
claimed. No Blender executable was available. A fresh Git clone failed because
`github.com` did not resolve in the container. Relevant pinned public sources were
read with the web tool; executable source was assembled from the supplied handoff
ZIPs and verified against their existing frozen-source hashes.

Environment measured here: Python 3.13.5, NumPy 2.3.5, OpenCV 4.13.0, Pillow 12.3.0.
Code's report uses Python 3.12.3 / NumPy 2.2.6. Workstation replay must use its
original environment; no dependency change is proposed. The audit rejects a
NumPy/OpenCV mismatch with saved prediction metadata.

## Executed checks

| Suite | Passed | Failed | Measured seconds |
|---|---:|---:|---:|
| Original FSG1 | 23 | 0 | 6.574 |
| Existing coverage audit | 29 | 0 | 7.174 |
| Existing HDR candidate | 34 | 0 | 8.985 |
| Existing prospective validation | 48 | 0 | 8.461 |
| New stage/visibility audit | 37 | 0 | 5.542 |

The original suite's additional repository-rig integration check remains for
Code's checkout (24 total there previously). Some timings overlap a separate
synthetic integration audit and are not workstation performance predictions.
Both new Python files passed `py_compile`.

All three new negative controls exited 1:

```
cap:    FAIL AssertionError: lower-cap classification lost its sign
replay: FAIL ValueError: replay mismatch in disparity; no counterfactual analysis authorized
cycle:  FAIL AssertionError: interpolated consistency does not establish endpoint consistency
```

Checks cover exact whole-image refinement replay, initial and unsupported-value
preservation, bound accounting, flat-signal denominators, signed cap separation,
undefined empty/constant statistics, unchanged final support across stage metrics,
input preservation, stale input and version refusal, no truth dependency in RGB
tracing, a deliberately injected accepted-occlusion row, strict JSON serialization,
seed-reference mismatch, overwrite refusal, and synthetic provenance rejection.
The cycle example deliberately constructs two wrong endpoint residuals whose
interpolation cancels; it does NOT establish the mechanism of the real two leaks.

## Full synthetic end-to-end exercise

The original analytic backend produced a FULL seed-17 three-case record and the
existing analytic validation backend produced FULL seed-31/73 two-case records.
Their original and HDR predictions were saved by the frozen tools. The new CLI
then audited all seven pairs / fourteen instrument-pair combinations, including
its full input/output path selection and same-support seed comparison.

```
[fsg-failure-audit] SUMMARY pairs=7 exact_replay=true inputs_unchanged=true
new_primary_samples=0 seconds=49.814 status=SYNTHETIC_AUDIT_NOT_A_RENDER_RESULT
```

Process exit: 0. All 159 synthetic input files hashed identically before/after.
No default, milestone or fusion flag was granted. The full analytic right-step
references contained 4,608 raw / 3,528 core singly-visible pixels per seed. The
analytic frozen predictions accepted no core points. The separate injected-leak
unit check exercised the reporting path despite that absence of real analytic
leaks. These are NOT Code's Cycles records or evidence that its leak disappeared.

The two instruments' `stage_visibility.png` output was produced for all pairs.
The seed-31 HDR step image was visually inspected: consistent panel layout,
accepted-support mask, stage errors, cap locations, truth-only occlusion strip,
and empty accepted-core panel. Missing pixels remain distinct through the
separate support panel; no depth interpolation or hole filling was performed.

## Development issues, preserved here

The first synthetic suite-generator call failed because its new test helper
called the original acquisition function with `spp=None`. The helper now supplies
the original profile's 64/256 sample count explicitly, matching the normal entry
point. No production code, estimator, fixture, or scientific threshold changed.

Two long foreground integration invocations were interrupted by the execution
wrapper's time limit and left incomplete NEW synthetic QA directories. Those are
not completed audit results and were not reused. A later unbroken invocation in
a fresh synthetic output directory completed in 49.814 seconds with the same
code and inputs. One combined regression command was likewise interrupted;
the outstanding suite was rerun separately and completed. This was execution
management, not a numerical or integrity failure of the audit.

## Interpretation limits

The 3.1234% cap calculation is a verified geometric arithmetic check, not a
measurement of the frozen Cycles disparity initialization or cap counts. Those
remain the central workstation question.

Raw and intermediate stage errors are evaluated on the final accepted support;
they are not evaluations of alternative complete pipelines. Cap membership,
gradient conditioning, and cycle endpoint statistics are not new rejection rules.
Truth-based tail groups and half-occlusion masks belong exclusively to evaluation.
Two seeds of one fixed geometry cannot calibrate general uncertainty or estimate
a universal false-acceptance rate.

The HDR bright-full synthetic stress failure and every historical real FSG1
failure remain unchanged. This package performs no new rendering and introduces
no candidate that could be adopted. Workstation results are pending.
