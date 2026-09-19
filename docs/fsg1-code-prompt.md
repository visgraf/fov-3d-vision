# Claude Code execution prompt - FSG1

You are the workstation Code surface for this repository. First read the CURRENT
`CLAUDE.md`, then `docs/fsg1-single-patch.md`. Chat has supplied the implementation;
your role is execution, diagnosis of genuine implementation failures, measured
write-up, commit/push, and a paste-ready report. Luiz has authorized this first
single-patch milestone only. Do not start fusion, surface growing, or a new phase.

## Non-negotiable experiment boundaries

Use Blender `pass_index` as oracle object identity, never as a depth shortcut.
Keep all output geometry in the fixed head/cyclopean frame H, not a rotating gaze
frame. Use RGB/calibration only for inference. Preserve the old Phase C/D code and
defaults. Keep generated renders, scenes, NPZ files and checks under `previews/`,
not in git.

This is a direct, padded perspective acquisition, not the original OSL retina.
No script is to upsample a peripheral sample and call it a new foveal observation.

Do not import host OpenCV, Pillow or OpenEXR into Blender's Python. Do not import
`bl_common` into the host interpreter; it imports bpy. `rig` is NumPy-only and may
be imported by both. A missing dependency is not evidence of a stereo failure.

Chat could not clone the repository in its execution sandbox. It read the public
main interfaces through the web tool, wrote an additive handoff, and tested 23
software checks without Blender. Therefore treat current-checkout integration and
all bpy API calls as unverified until you run them. The installer's log entry
records the actual destination HEAD. Do not imply the Chat fixtures were renders.

## Cost discipline

Class estimates below are scheduling estimates, NOT timings measured on this
workstation. No uniform panoramic reference, external dataset, asset download or
large scan is needed. If a command threatens to exceed 5 minutes, stop and report;
do not silently promote it to overnight. In particular do not silently fall back
to a long CPU run. The renderer requires explicit `--device CPU` for that choice.

Save stdout/stderr for each command. Use bash `set -o pipefail` for tee pipelines.
Retain old failed output directories; a corrected run gets a new suffix.

## 1. Preflight - Interactive (environment installation may be Batch)

Record branch, HEAD, dirty status and environment versions before editing.
Confirm this handoff was committed on main. If the working tree has unrelated
changes, stop rather than staging or overwriting them.

```bash
git status --short
git rev-parse HEAD
blender --version
.venv/bin/python -c "import sys,numpy,PIL; print(sys.version); print('numpy',numpy.__version__,'Pillow',PIL.__version__)"
.venv/bin/python -m pip list | grep -Ei 'opencv|numpy|pillow'
```

If there is exactly one working OpenCV installation already, record its version
and do not stack another distribution over it. If there is none, install the
add-on into the existing host venv:

```bash
.venv/bin/python -m pip install -r requirements-fsg.txt
```

Do not upgrade/downgrade the existing NumPy/Pillow pins without a separately
explained dependency diagnosis. If multiple OpenCV packages share `cv2`, diagnose
the environment rather than blindly uninstalling packages from unrelated projects.
The handoff was exercised with OpenCV 4.13.0; record any difference.

## 2. Geometry/software checks - Interactive (measured ~3 s in Chat)

```bash
mkdir -p previews/fsg1
.venv/bin/python tools/rig.py --self-test
.venv/bin/python tools/fsg_geometry.py --self-test
.venv/bin/python tools/fsg_scene.py --self-test
.venv/bin/python tools/dev/check_fsg.py --self-test --repo-check --report previews/fsg1/software-checks.json
```

Expected: 24 checks pass with `--repo-check` (Chat's 23 plus the actual repository
rig integration check); no Blender measurement is claimed. The suite internally
uses a temporary analytic backend, exercises the real acquisition orchestrator,
reads/writes the real file formats, performs stereo/evaluation, deletes the truth
from the inference path and verifies identical arrays, then cleans its own temp
files. Its temporary synthetic gate failures used as controls are expected only
where the suite explicitly asserts them; the suite's final failed count must be 0.

Run each deliberate negative separately; BOTH must return exactly 1 with the
specified geometry failure, not a dependency/import error:

```bash
.venv/bin/python tools/dev/check_fsg.py --negative baseline
.venv/bin/python tools/dev/check_fsg.py --negative crop
```

Expected lines begin `[fsg-check] FAIL deliberate baseline mutation` and
`[fsg-check] FAIL deliberate crop mutation`. Preserve them and their exit codes
in the report as EXPECTED negatives. A negative that exits 0 is an unexpected
check failure: stop.

## 3. Real small-profile acquisition - Batch (estimated <5 min on the GPU)

Use a NEW output directory. The tool intentionally refuses nonempty destinations.
Set a suffix such as `-fix1` after any code correction and preserve the first run.

```bash
SMALL=previews/fsg1/small-seed17
blender -b --python-exit-code 1 -P tools/fsg_render.py -- --out "$SMALL" --profile small --device OPTIX --seed 17 --save-blend
```

Expected before any empirical stereo judgment:

* a real Blender version/backend in every acquisition.json, never synthetic_stub;
* all camera projection checks <=0.002 px and ray-cast checks <=20 micrometres;
* correct object IDs at all cross-checked rays;
* independent L/R seeds, no adaptive sampling/denoising/DOF/motion blur;
* 3 completed cases with 320x320 raw RGB per eye, 64 spp unless the repository's
  declared profile has changed (a changed convention requires reporting);
* `run.json` complete marker, written only after all cases succeed;
* 39,321,600 primary camera samples for the prescribed default suite.

These sample totals are arithmetic, not performance claims. Record the actual
render/annotation/total times. A zero shell exit from Blender alone is insufficient:
read the console, confirm the COMPLETE marker and inspect the output files. The
script also hard-exits nonzero on failure, and `--python-exit-code 1` is a second
guard. Do not treat a partial directory as a complete acquisition.

## 4. Real small-profile stereo/evaluation - Interactive (estimated <10 s)

```bash
.venv/bin/python tools/fsg_stereo.py "$SMALL"
.venv/bin/python tools/fsg_evaluate.py "$SMALL"
```

Never use `--allow-synthetic` for a workstation experiment. That flag exists only
for analytic software fixtures and cannot authorize the milestone.

Read every metrics.json, including `per_object_interior`, `boundary` and
`singly_visible`, not just the pooled summary. The declared interior targets are
>=90% coverage, <=1% median relative left-eye range error, <=3% p95 relative error.
At this stage a pass is `SMALL_PROFILE_PASS`, not the final experiment result.

Inspect the saved rectified RGB pair, validity, predicted and reference range,
relative error and reference masks. Inspect `points_head.ply` in a suitable viewer
or Blender (import as points; there are no faces). Check the two depth levels of
the step, the tilt, and the fixed head axis convention. Do not mistake Blender
world +Y for head -Z.

If a numerical gate fails, diagnose the cause before editing. A plainly identified
API, image orientation, indexing or calibration bug may be fixed outside the
checks, with its cause recorded. Otherwise STOP and report the miss to Luiz/Chat;
do not tune the matcher or scenes until the criteria pass. Do not proceed to a
full run merely to hide a small-profile failure.

## 5. Real full-profile acquisition and evaluation - Batch (estimated <5 min GPU)

Proceed only after the small run and software checks pass, with no unexplained
geometry or image-orientation issue.

```bash
FULL=previews/fsg1/full-seed17
blender -b --python-exit-code 1 -P tools/fsg_render.py -- --out "$FULL" --profile full --device OPTIX --seed 17 --save-blend
.venv/bin/python tools/fsg_stereo.py "$FULL"
.venv/bin/python tools/fsg_evaluate.py "$FULL"
```

Expected default raw image 640x640, accepted core 256x256, 256 spp, total prescribed
suite cost 629,145,600 primary camera samples. The same fixed physical head/baseline
and fixtures are used. Full must pass the same interior criteria per case and per
instance, with a doubled pixel boundary margin to preserve its angular width.

`MILESTONE_PASS` requires a real full-profile suite at the recorded profile default
spp. An explicit sample-count override is diagnostic only and produces a different
status. Even a pass is limited to these controlled opaque textured fixtures; it
is not a claim about complex scenes, full objects, or the original OSL sensor.

## Likely failures and where a fix belongs

| Likely issue | Diagnostic / implementation location |
| --- | --- |
| cv2 missing or conflicting wheels | Host venv only; preserve existing project dependencies |
| Evolving Blender node, image-save, or look API | `BlenderBackend` in `tools/fsg_render.py`; do not change acceptance thresholds |
| GPU backend unavailable | Check Cycles preferences/device; no silent CPU full run |
| Projection/ray-cast invariant fails | Blender camera setup or exported-mesh/frame conversion in `fsg_render.py`; compare to current rig.py before touching anything |
| RGB upside down or nonlinear EXR interpretation | Single-layer EXR save/readback in `fsg_render.py`; use tilted case as a control |
| Scale or principal-point/crop error | `fsg_geometry.py` and `fsg_stereo.py`; rerun exact positives and both negatives |
| Real stochastic RGB too noisy / local texture insufficient | Report measured rejection and errors, inspect RGB and disparity_sgbm vs refined; NOT permission to replace data with truth or tune arbitrary parameters |
| Mask-edge and half-occlusion failure | Report boundary/singly-visible results; no larger truth-based exclusion to conceal it |
| Existing output directory | Choose a new suffix; preserve original records |

Prohibited fixes: editing the checks, acceptance thresholds, reference denominator,
calibration fixtures, baseline, sample profiles, image masks, boundary margins,
search limits, refinement bounds, or input provenance to manufacture a pass. Do
not silently retune SGBM. Do not replace RGB-derived disparity with render depth.
If a CHECK itself appears wrong, stop and describe the counterexample for Chat
and Luiz rather than editing it.

## 6. Write up, commit, push, report - Interactive

Fill ONLY the Workstation Results section of `docs/fsg1-single-patch.md` with actual
file-derived values. Keep the separate Chat/synthetic validation section intact.
Append a dated entry to `docs/log.md`, update the FSG1 README row added by the
installer, and annotate D-FSG1 with outcome/evidence if appropriate. Do not declare
a next phase or authorize fusion; that decision belongs to Luiz.

Run the software suite again after a code fix. Check `git diff --check`, inspect
all staged files, and do not commit artifacts under previews. Commit your justified
code fixes and measured write-up, then push to main as the working agreement
specifies. Report a push failure honestly rather than implying it succeeded.

Return this paste-ready block, with summary lines VERBATIM and every FAIL line:

```
FSG1 WORKSTATION REPORT
HEAD before / after:
Branch / push result:
Blender / GPU backend:
Host Python / NumPy / OpenCV / Pillow:
Commands and exact output directories:
Software-check SUMMARY:
Expected negative baseline: exit code + verbatim FAIL line
Expected negative crop: exit code + verbatim FAIL line
Per-eye max projection px / ray-cast m / checked hits (file paths):
Small per-case and per-instance coverage / median / p95 (file paths):
Full per-case and per-instance coverage / median / p95 (file paths):
Boundary and singly-visible observations (file paths):
Actual camera samples / render seconds / oracle seconds / stereo seconds:
Visual files actually inspected and what was observed:
UNEXPECTED FAIL lines (all, or none):
Code changes: file + diagnosis + one-sentence fix (or none)
Checks/thresholds modified: no (otherwise stop and explain)
Final evaluator status verbatim:
Stopped after FSG1; no fusion or policy implementation:
```
