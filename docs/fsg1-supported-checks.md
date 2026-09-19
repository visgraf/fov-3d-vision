# FSG1f Chat validation record

Date: 2026-09-19. The delivered estimator is UNTESTED on the workstation's Cycles
observations. Everything below is software or analytic-fixture evidence.

## Environment and source access

- Python 3.13.5, NumPy 2.3.5, OpenCV 4.13.0, Pillow 12.3.0.
- No Blender executable, GPU rendering, or real acquisition was used.
- A fresh Git clone failed because github.com could not be resolved in the
  execution container. The working agreement and pertinent public source were
  read at `7073594` through the web tool. Execution used the source from the
  supplied original and FSG1b/c/d/e handoff archives. The eleven pre-existing
  frozen dependency hashes and structural equivalence checks passed.
- Code must keep its original NumPy 2.2.6/Python 3.12.3 environment when replaying
  its observations. Chat's synthetic predictions are not workstation baselines.

## Software results

| Suite | Passed | Failed |
|---|---:|---:|
| Original FSG1 (without unavailable checkout rig integration) | 23 | 0 |
| FSG1b coverage audit | 29 | 0 |
| FSG1c HDR | 34 | 0 |
| FSG1d prospective validation | 48 | 0 |
| FSG1e stage/visibility audit | 37 | 0 |
| New FSG1f supported candidate | 46 | 0 |

The new suite completed in 4.112 seconds on its final recorded run. The
workstation runs the additional original `--repo-check` against its real rig.
All three new Python files compiled successfully.

New checks include exact first-stage arithmetic, the original candidate remaining
unchanged, safe handling of zero and tiny positive interpolation weights, endpoint
cancellation, a perfectly reciprocal isolated wrong match, correct constant-field
support, border support, no output from blank observations, nested ablation masks,
NaNs where rejected, immutable inputs, truth-free reconstruction, exact stored
replay, and the original zero-core-leak safety requirement.

A limitation is deliberately tested: an extended coherent disparity field can
pass the support rule even if its putative depth is wrong. The new rule is NOT
an oracle visibility classifier.

## Deliberate negatives

All four exited 1:

```text
iterations: AssertionError: first update must equal stage 1, not the old three-update result
cycle: AssertionError: averaged cancellation must not pass the endpoint gate
footprint: AssertionError: isolated endpoint agreement does not establish patch support
replay: ValueError: replay mismatch in disparity_px; no counterfactual analysis authorized
```

The exact same negative conditions also appear as expected failures inside the
self-test; no production or reference threshold was relaxed.

## Full synthetic integration

The existing analytic backends generated the three original full seed-17 pairs
and two validation pairs at each of seeds 31 and 73. They sample procedural
textures and add simple synthetic noise. They do not simulate Cycles light
transport, specularity, view-dependent appearance or all boundary effects.

Both old baselines were generated with the frozen source on those synthetic
observations. The final comparator then replayed both exactly on all seven pairs,
wrote all three new variant predictions before evaluation geometry, and evaluated
the variants on the original fixed references.

Final command status: exit 0, `SYNTHETIC_COMPARISON_NOT_A_RENDER_RESULT`.
Runtime: 38.389 seconds. Candidate numerical gates: all pass on these analytic
fixtures. Milestone/default/fusion flags: all false. New primary samples: zero.
All 145 input files remained byte-identical, including an independent second
rehash outside the comparison program.

Candidate results, PERCENT, synthetic only:

| Fixture / instance | Coverage | Median range error | P95 |
|---|---:|---:|---:|
| Original fronto | 99.263 | 0.113 | 0.383 |
| Original tilted | 99.210 | 0.125 | 0.528 |
| Original step foreground | 99.601 | 0.066 | 0.256 |
| Original step background | 99.655 | 0.241 | 0.728 |
| Seed 31 tilted holdout | 99.777 | 0.142 | 0.575 |
| Seed 31 right-step foreground | 99.968 | 0.116 | 0.337 |
| Seed 31 right-step background | 94.907 | 0.148 | 0.621 |
| Seed 73 tilted holdout | 99.814 | 0.145 | 0.580 |
| Seed 73 right-step foreground | 99.972 | 0.118 | 0.331 |
| Seed 73 right-step background | 94.898 | 0.147 | 0.616 |

Each new right-step fixture has 4,608 raw singly visible pixels and 3,528 core
pixels. The candidate accepts zero in both populations in this analytic run.
The old analytic HDR baseline also had no core leak; this does NOT demonstrate
removal of the actual two Cycles HDR leaks. The unit tests separately exercise
cancellation and an isolated self-consistent false cycle.

The image `supported_comparison.png` for the full synthetic seed-31 right-step
was inspected visually. The candidate's rejected vertical band is wider than the
baseline's; the error and missing-support panels are kept separate. That visible
coverage cost is intentional and counted, not hidden by changing the reference.

## Development interruptions and code adjustments

The first self-test passed. A copied refiner docstring was then corrected to say
ONE update, and its structural equivalence test was updated to allow only that
explanatory text change as well as the iteration count. Arithmetic did not change.

A combined regression/negative command exceeded its execution-wrapper time limit
after the regression summaries were complete. The negatives and compilation
were subsequently executed separately and completed.

Several synchronous full integration invocations were interrupted by the wrapper
before they produced a suite summary. Their partial outputs were preserved; they
are not claimed as successful runs. Before the final completion, the new comparison
wrapper was optimized to compute each immutable ray/mesh reference once per pair
rather than for every instrument. A new software check independently verifies
that all reused-reference metrics/fails equal the original evaluator's result
for all three variants. No reference, estimator, footprint, tolerance, cap,
texture, seed or fixture was changed.

The final complete invocation was allowed to finish and its exit status and
summary were checked. The reported integration numbers come ONLY from that final
complete directory, not from selecting among the interrupted results.

## Remaining uncertainty

- The actual Cycles observations and their leakage locations were not available
  here. No success on them is claimed.
- One update still uses the original potentially ill-conditioned denominator.
  It is a data-motivated bounded candidate, not a complete optimization remedy.
- The two-sided footprint rule can cost too much coverage on real images. Its
  full synthetic right-step background coverage is already only about 94.9%.
- Thin or partially supported structures can be rejected; coherent wrong fields
  can survive. It is not a general occlusion solver.
- Small-profile and bright-full stress failures from earlier work remain on
  record. They were not redefined or erased by this full-record comparison.
- The former prospective seeds are now diagnostic data. A future candidate pass
  on them cannot be relabeled prospective validation.
- No actual GitHub-checkout application, Blender integration or new rendering
  has been validated in this container.
