# FSG1c validation by Chat - measured software results and limits

Date: 2026-09-19. This is NOT a Blender or workstation measurement.
No real Code observation arrays were available here. The supplied audit report
was read, not independently reproduced. Its reported commit is 64e02af.

## Source basis and environment

The working agreement and current FSG1 source interfaces were read from the
public repository. A network clone attempt failed with `Could not resolve host`.
The supplied original FSG1 and FSG1b ZIPs were therefore extracted into a scratch
source tree. The four numerical source SHA-256s match the frozen audit hashes
exactly. No claim of testing a live Git checkout or the optional rig integration
is made. Code must repeat checks on the actual checkout and existing interpreter.

Sandbox: Python 3.13.5, NumPy 2.3.5, OpenCV 4.13.0, Pillow 12.3.0. The reported
workstation is Python 3.12.3 and NumPy 2.2.6; keep its pins. Exact replay is
required on the workstation, never presumed across different environments.
No bpy module was present. No GPU, Cycles, Blender API or Blender acquisition
was executed. SyntheticBackend exercises file/geometry/stereo orchestration only.

## Checks actually run

```text
[fsg-check] SUMMARY passed=23 failed=0 seconds=2.729 blender_executed=False
[fsg-audit-check] SUMMARY passed=29 failed=0 seconds=2.774 blender_executed=False
[fsg-hdr-check] SUMMARY passed=34 failed=0 seconds=3.316 blender_executed=False
```

The optional workstation rig integration is the 24th legacy check and was NOT
run here. All three new Python files compile.

All three deliberate negative commands returned exit 1:

```text
[fsg-hdr-check] FAIL AssertionError: distinct HDR inputs collapsed; pre-quantization clipping returned
[fsg-hdr-check] FAIL ValueError: replay mismatch in valid; no counterfactual analysis authorized
[fsg-hdr-check] FAIL AssertionError: deliberate 20-percent range error: median_relative_range_error=0.19999999999999996 fails max 0.01; p95_relative_range_error=0.19999999999999996 fails max 0.03
```

The production CLI refused analytic input without --allow-synthetic, exit 1:

```text
[fsg-hdr] FAIL ValueError: not a checked Blender record; synthetic inputs forbidden here
```

The analytic bright-full numerical miss completed its comparison and returned
exit 2, distinguishing a scientific miss from an integrity/software failure:

```text
[fsg-hdr] SUMMARY runs=1 inputs_unchanged=true new_primary_samples=0 all_requested_candidate_gates_pass=false seconds=4.833 status=CANDIDATE_COMPARISON_COMPLETE_NOT_A_MILESTONE
```

The tests cover monotone/fixed radiometry and HDR values; no image-statistic or
eye-dependent adaptation; constant dark/bright inputs yielding no accepted
geometry; known bright tilted geometry; candidate frame/depth properties;
unchanged legacy source/globals/results; exact replay; wrong-depth input rejection;
removing ground truth without changing candidate arrays; file preservation;
forbidden/overwritten outputs; stale inputs; synthetic provenance refusal;
unchanged gate sensitivity; exact support partitions and empty half-occlusion
labels; visible artifacts; and non-promotion of synthetic results.

## Analytic numerical diagnostics - not claimed Cycles accuracy

The existing analytic backend was run at small and full. A separate bright stress
uses the SAME analytic RGB followed by the fixed transformation 1.2 + 2*RGB on
both eyes. This is not a change to the experimental Blender fixtures. The bright
stress is intentionally all above the old scene-linear clamp. At small, its
three cases pass the numerical gates in the software test (the tilted example
has 97.803% coverage, 0.385% median and 1.433% p95 error).

The following are measured candidate results from supplementary full diagnostics.
All errors are relative left-eye range, in percent, on accepted interior pixels.

| Analytic full record | Case/population | Coverage % | Median error % | P95 error % | Numerical outcome |
| --- | --- | ---: | ---: | ---: | --- |
| Standard | fronto | 99.156 | 0.317 | 1.161 | Pass |
| Standard | tilted | 99.103 | 0.345 | 1.386 | Pass |
| Standard | step pooled | 99.575 | 0.237 | 1.304 | Pass |
| Standard | step foreground | 99.547 | 0.162 | 0.676 | Pass |
| Standard | step background | 99.618 | 0.470 | 1.685 | Pass |
| Bright stress | fronto | 79.097 | 0.334 | 1.161 | FAIL coverage |
| Bright stress | tilted | 78.828 | 0.370 | 1.467 | FAIL coverage |
| Bright stress | step pooled | 86.809 | 0.243 | 1.419 | FAIL coverage |
| Bright stress | step foreground | 85.760 | 0.163 | 0.680 | FAIL coverage |
| Bright stress | step background | 88.388 | 0.509 | 1.859 | FAIL coverage |

The baseline encoder accepts zero pixels in the artificial bright stress.
Recovering many points while still failing coverage is NOT a pass. No alternative
curve, gain, cutoff, window or truth-dependent correction was tried to erase that
miss. The candidate remains exactly the declared x/(1+x) encoding.

The three-run standard-small/standard-full/bright-full comparison took 11.341 s
in this sandbox, including replay, file checks and artifact generation. That
runtime is a software measurement, not a workstation timing estimate. New
primary camera samples were zero, and all input hashes remained unchanged.

### Why ship the candidate despite the stress miss?

The purpose is to measure ONE mechanism change on the actual existing records,
not assert a universal solution. The stress demonstrates an unresolved limit of
the eight-bit fixed-window representation. The actual Cycles records have not
been measured here and can differ in radiance/gradient distributions. This
failure is disclosed before execution and prevents an unqualified claim even
if the old full seed-17 record passes. Comparing it costs no new acquisition.
A negative actual result is a valid reason to stop and choose another explicit
intervention, not an invitation for Code to tune this one.

## Visual inspection and warnings

`qa/comparison/bright-full/step/comparison.png` was opened and inspected in the
sandbox: the old display is flat white, the candidate reveals low-contrast
structure, accepted support is substantially recovered but holes remain, and
those holes are separately shown rather than hidden by a depth image. Labels
and all nine panels fit. This is an ANALYTIC image, not the user's audit figure
or a new Blender render.

A NumPy invalid-matmul RuntimeWarning occurs in the unchanged audit/geometry
path when tracing deliberately unsupported zero-disparity analytic samples.
The invalid samples remain masked; finite accepted-point and provenance checks
pass. The warning is not concealed or reclassified as a measurement. There
were no unexpected failing software checks. The bright-full coverage misses
above are real numerical failures of that software stress, not software-check
failures and not results on the actual observation files.

## Reproduction of the supplementary stress

Within a scratch Python process using the repository tools:

```python
from pathlib import Path
import sys
sys.path[:0] = ['tools', 'tools/dev']
import fsg_render as r
import fsg_stereo as s
import fsg_hdr_compare as c
from check_fsg_hdr import BrightBackend

run = Path('previews/fsg1c-software-bright-full')  # must not exist
args = r.parse_args(['--out', str(run), '--profile', 'full'])
args.spp = 256
r.acquire(args, BrightBackend())  # analytic backend, NOT Blender
for case in ('fronto', 'tilted', 'step'):
    s.process_pair(run / case)
c.compare([run], Path('previews/fsg1c-software-bright-comparison'),
          allow_synthetic=True)
```

This supplementary stress reproduction is optional and software-only. It is not
an authorization for another real acquisition or a threshold/fixture edit.

## Still pending

Actual interpreter/rig integration; replay of all nine original Blender cases;
actual candidate coverage/accuracy/score distributions; review of actual
candidate artifacts; independent geometric/photometric validation; nonzero
half-occlusion test; and any fusion or surface-growing experiment. The existing
source records informed this candidate, so their comparison is development-set
evidence even with unchanged numerical targets.
