# FSG1d handoff validation - Chat sandbox

## Scope and environment

Measured here: software behavior, synthetic acquisition orchestration, fixed
geometry/reference masks, paired inference/evaluation, file integrity controls,
negative tests, and diagnostic image layout. **No Blender executable was
available. No real Cycles acquisition or workstation observation was tested.**

This sandbox could read pinned public repository files through the web tool,
including `CLAUDE.md`, but `git clone` failed with DNS resolution of github.com;
a direct file download also failed. Local dependencies were recovered from the
original uploaded handoff ZIPs. Their source hashes are pinned at runtime;
Code must verify them against its actual checkout. No fresh full repository
checkout or workstation rig-integration check was possible here.

The sandbox used Python 3.13.5, NumPy 2.3.5, OpenCV 4.13.0, and Pillow 12.3.0.
The workstation report lists Python 3.12.3 and NumPy 2.2.6. Do not upgrade the
workstation to match this sandbox. Re-run all checks in its existing environment.

## Software results

The final executions produced:

```text
[fsg-check] SUMMARY passed=23 failed=0 seconds=3.549 blender_executed=False
[fsg-audit-check] SUMMARY passed=29 failed=0 seconds=3.730 blender_executed=False
[fsg-hdr-check] SUMMARY passed=34 failed=0 seconds=4.486 blender_executed=False
[fsg-validation-check] SUMMARY passed=48 failed=0 seconds=4.110 blender_executed=False
```

The legacy 24th check is workstation rig integration and remains for Code.
All four new scripts compiled with `py_compile`.

New checks cover fixed sources, the one-change HDR kernel, renderer AST
agreement, profile/seed restrictions, new texture determinism, per-instance
reference presence, nonempty left-eye half-occlusion, known-correct geometry,
wrong geometry and identity handling, source/input preservation, predicted
artifact creation, and reconstruction with all evaluator geometry removed.
A fresh interpreter confirmed that importing the Blender-side new module does
not require OpenCV or Pillow. The synthetic backend has an explicit false
Blender provenance and cannot produce a real validation pass.

Three deliberately faulty invocations each exited 1:

```text
visibility: [fsg-validation-check] FAIL ValueError: half-occlusion NOT_EXERCISED: raw reference too small
leakage: [fsg-validation-check] FAIL AssertionError: accepted 1 singly-visible core pixels; limit=0
geometry: [fsg-validation-check] FAIL ValueError: exported Blender mesh disagrees with frozen validation specification
```

The visibility negative uses the old foreground-left step: it demonstrates that
reusing the earlier unexercised fixture cannot silently pass the new test.
The leakage negative accepts just one known monocular-core pixel. The geometry
negative shifts the prescribed surface by 0.1 m.

## Analytic full-record plumbing test - NOT a renderer result

After freezing the geometry, sampling schedule and unchanged instrument, the
new acquisition and evaluation paths were exercised with a test-only analytic
texture sampler plus small independent additive noise. It does not model
lighting, HDR radiance, Cycles stochastic transport, optics, or Blender APIs.
No parameters were changed in response to its accuracy results.

Both prospective full seed paths completed. These are the measured **synthetic**
interior results (percentages):

| Seed | Surface | Coverage | Median relative range error | P95 |
|---:|---|---:|---:|---:|
| 31 | New tilted plane | 99.744% | 0.341% | 1.457% |
| 31 | Right foreground | 99.956% | 0.208% | 0.780% |
| 31 | Background | 96.723% | 0.434% | 1.939% |
| 73 | New tilted plane | 99.768% | 0.346% | 1.451% |
| 73 | Right foreground | 99.964% | 0.211% | 0.789% |
| 73 | Background | 96.619% | 0.432% | 1.894% |

The process emitted `SYNTHETIC_VALIDATION_NOT_A_RENDER_RESULT`, never a real
validation pass. Its paired evaluation took 11.682 s in this sandbox. That time
is not a workstation or Blender timing prediction.

The analytic geometry produces 4,608 raw singly visible reference pixels and
3,528 fixed-core pixels per full step. Both synthetic candidates accepted zero
of either population. At small, the corresponding counts are 1,280 and 1,008.
The tilted case has no singly visible population and reports `NOT_EXERCISED`.
These counts validate that the new fixture exercises the intended geometry;
they do not measure a real renderer's correspondence rejection.

The new software smoke test also completed at small: new tilted plane
100.000%/0.565%/2.047%, right foreground 100.000%/0.394%/1.030%, background
94.291%/0.427%/1.691% for coverage/median/P95. This does not supersede any old
small-profile Cycles failure.

The full seed-31 step and tilted diagnostic images were opened and inspected.
The step's missing band coincides with the independently selected occlusion
strip; the unsafe-core panel is empty. The tilted image explicitly has no
occlusion reference. These are analytic software visuals, not photorealistic
observations. Error panels must always be read alongside validity masks.

## Development changes and limitations

The first new check run passed 46/46. A subsequent source review identified a
portability issue in the new exported-mesh guard: it should accept either legal
quad diagonal, not require the analytic triangle tessellation. The guard was
made topology-aware and two controls added, giving the final 48/48. No estimator,
fixture geometry, sampling parameter, reference definition or numeric threshold
was changed. No real acquisition occurred during development.

The older FSG1c analytic bright-full coverage failure remains unresolved and
unchanged. Passing the new analytic plumbing tests does not cancel it: these
fixtures have a different radiometric distribution. The actual new Cycles
results are unknown.

The experiment remains limited to two opaque textured planar configurations,
known poses, fixed head centres, and oracle segmentation. A zero-leakage result
under these conditions is not general occlusion handling, self-occlusion of a
complex object, boundary completeness, or calibrated per-point uncertainty.

## Artifact validation

The deliverable contains six new files only: four Python modules/checks and two
Markdown documents. No existing file is replaced, and no generated image,
observation or point cloud is installed. The ZIP uses repository-relative paths.
Archive membership/CRC, extraction into a temporary directory, byte identity,
Python compilation of extracted scripts and shell-command syntax are checked
before delivery. A checksum and four-line guarded apply block accompany it.
