# FullScene-REAL-1 — End-to-End Frozen-System Benchmark

## Purpose

FullScene-REAL-1 is the first deliberately end-to-end field run of the current
foveal stereo system on the Blender test scene. It is not another one-object
causal probe. The whole point is to discover what the assembled observer
actually produces when it is asked to process the scene as a scene.

The experiment starts from the completed FullScene-1d calibration state
(commit `651a6cb`) but **does not reuse the already reconstructed object maps as
input**. REAL-1 is a fresh benchmark run from the Blender scene.

The benchmark question is:

> What RGB-D / geometric scene representation does the frozen current system
> produce when every positive-instance benchmark object is attempted once, and
> where do attention, measurement, geometry and control debts remain?

## What is frozen

REAL-1 must reuse the established mechanisms rather than improving them during
the run:

- current stereo front end;
- `tools/scene_render_fix.py` generic acquisition path;
- frozen FSG6f local controller through `tools/multiobject2c_policy.py`;
- 12 mm surfel association;
- inherited `<100` valid-target-point empty-look / negative-evidence semantics;
- 24 selected-object-fixation watchdog including the seed;
- established cyclopean / MultiObject epistemic audit semantics;
- the already demonstrated *single* epistemic handoff, when warranted.

No pre-REAL-1 source is to be edited. Repository-specific integration belongs
in the new `fullscene_real1_*` files only unless Chat explicitly approves a
change later.

## What is deliberately oracle-assisted

REAL-1 is **not a discovery benchmark**. The Blender scene may provide positive
instance IDs and a seed direction/bounds cue so that every benchmark object is
attempted. This is consistent with the project's current oracle-instance stage,
but it must be recorded explicitly.

The stronger evaluator oracle — reference depth / surface geometry — is
quarantined from control. The observer state must be sealed before evaluator
truth is rendered/opened.

Therefore REAL-1 measures the quality of the current reconstruction/control
pipeline **conditioned on object enumeration**, not autonomous object discovery.

## Object loop

For each dynamically enumerated positive instance ID, in deterministic order:

1. compute a benchmark seed direction without using reference depth;
2. take exactly one seed fixation with the existing acquisition/stereo path;
3. if usable selected-object geometry exists, grow with frozen FSG6f until:
   - `no_frontier`, or
   - the 24-fixation object watchdog;
4. audit the final object state read-only;
5. if and only if the object ended in genuine `no_frontier` **and** the audit
   reports exterior `NEVER_OBSERVED > 0`, permit one established cyclopean
   handoff and at most one returned local action;
6. audit the post-handoff state once more if a handoff occurred;
7. freeze the object status and move on.

There is no recursive handoff scheduler and no second-pass revisit scheduler in
REAL-1.

## Object status is descriptive, not a score

At minimum the final scene table must distinguish states such as:

- `NOT_VISIBLE_OR_NO_TARGET_SUPPORT`
- `SEED_MEASUREMENT_FAILED`
- `WATCHDOG_REACHED_RETAIN_FOR_REVISIT`
- `POLICY_EXHAUSTED_WITH_UNSEEN_TERRITORY`
- `ATTENTION_COMPLETE_MEASUREMENT_PARTIAL`
- `LOCAL_FRONTIER_AND_ATTENTION_RESOLVED_UNDER_CURRENT_REPRESENTATION`
- `LOCAL_GROWTH_STOPPED_OTHER`

Do not collapse attention, measurement, geometry and control progress into one
quality/completeness score.

## Scene products

Before evaluator truth is opened, export the observer products:

- per-object NPZ and PLY geometry;
- combined `scene_points.npz` and `scene_points.ply`;
- sparse equirectangular observer depth panorama;
- sparse observer instance panorama;
- valid mask and depth preview;
- fixation history;
- per-object status table;
- sealed observer manifest.

The observer panorama is produced by projecting final observer geometry to the
cyclopean sphere with a documented nearest-range z-buffer. Missing geometry
remains missing; do not fill it from truth.

If actual surfel RGB is not carried by the current representation, do not fake
photometric color. Instance-color visualization is fine, but must be labeled as
such.

## Evaluator products — strictly after observer seal

After `observer_complete.json` has been written and hashed, generate/reference:

- `reference_rgb.png`
- `reference_depth.npy`
- `reference_instance.npy`

Then compute, at least:

- oracle-visible/enumerated/attempted/instantiated inventory;
- per-object fixation counts and statuses;
- per-object surfel counts and spherical footprint;
- reconstructed angular coverage relative to reference instance support;
- median and P95 absolute depth error where both reconstructed/reference depth
  are valid;
- purity/contamination where evaluable;
- attention residue and measurement residue;
- watchdog / local-stop / handoff counts;
- total wall time and Blender-launch count.

Truth may evaluate the frozen observer, never repair it.

## Checkpoint / resume requirement

A real scene run may take many Blender launches. Each completed object must
therefore have an `object_complete.json` checkpoint. `--resume` must skip
completed objects without rerendering them and continue global-step numbering.

The final observer state is sealed once. A sealed run must not silently resume
into additional control actions.

## Branch discipline

Create a new branch from the completed FullScene-1d result:

```bash
cd /home/lvelho/rd/fov-3d-vision
git switch fullscene-calibration-1
git pull
git switch -c fullscene-real-1 651a6cb
git push -u origin fullscene-real-1
```

`main` remains at the MultiObject-3h development line and
`fullscene-calibration-1` remains the calibration lineage. REAL-1 work and
results go only to `fullscene-real-1`.

## Implementation seam

`tools/fullscene_real1_run.py` already contains the benchmark state machine and
truth-sealing order. The one repository-specific integration seam is
`tools/fullscene_real1_repo_adapter.py`.

Claude Code is explicitly authorized to complete/fix the new REAL-1 files
against the live repository. It is **not** authorized to modify established
pre-REAL-1 policy, stereo, rendering, fusion or audit sources merely to make the
benchmark convenient.

This is deliberate: the benchmark asks what the existing system can do, not
what we can make it do after seeing the whole scene.
