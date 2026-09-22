# FullScene-REAL-1 — End-to-End Frozen-System Benchmark

## Blocker repair: procedural fixture, not `.blend`

The first REAL-1 prospective package made one false interface assumption: it
required a `.blend` input. The established FullScene/Reality lineage does not
load one. `tools/scene_render_fix.py` renders the procedural Reality-1 fixture
named `tabletop_cloth`, built from the evaluator-side scene specification.

REAL-1 therefore binds to a **fixture name**, not a file path. Provenance is the
fixture name plus the established evaluator scene-spec `truth_digest()`. It must
never record a `.blend` hash for a file the renderer does not consume.

## Purpose

REAL-1 is the first deliberately end-to-end field run of the current foveal
stereo system on the established procedural test fixture. It begins from the
completed FullScene-1d calibration state but does **not** reuse the reconstructed
object maps as reconstruction input.

The benchmark asks:

> What geometric/RGB-D scene representation does the frozen current system
> produce when every benchmark object is attempted once, and where do attention,
> measurement, geometry and control debts remain?

## The pre-control enumeration oracle

REAL-1 is not an autonomous discovery benchmark. To guarantee that every
benchmark object is attempted, a **quarantined REAL-1-only helper** may inspect
the evaluator-side procedural scene specification before control.

This is an explicit declassification boundary. The helper may output only:

- `object_id`
- `seed_yaw_deg`
- `seed_pitch_deg`
- `label`

It may use exact procedural geometry internally to derive the seed direction,
but vertices, surfaces, depth, normals, range, masks, coverage, or object extent
must not cross into the observer process.

`tools/fullscene_real1_oracle_scaffold.py` is the only new REAL-1 module allowed
to import the evaluator-side scene specification before observer control.
`fullscene_real1_run.py` and `fullscene_real1_repo_adapter.py` consume only the
sanitized `enumeration_oracle.json`.

This makes the benchmark statement precise:

- object discovery is **not** tested;
- object identity and one seed direction are oracle scaffolding;
- stereo reconstruction, fusion, local growth, stopping, audit and handoff do
  not receive exact evaluator geometry/depth truth.

## What remains frozen

The benchmark continues to reuse unchanged:

- `tools/scene_render_fix.py` procedural acquisition path;
- current stereo front end;
- frozen FSG6f via `tools/multiobject2c_policy.py`;
- 12 mm surfel association;
- `<100` valid-target-point empty-look semantics;
- 24 selected-object-fixation watchdog including seed;
- established epistemic audit semantics;
- at most one already-demonstrated epistemic handoff when warranted.

No pre-REAL-1 source may be edited merely to make the benchmark run.

## Object loop

For each sanitized oracle row, sorted by positive instance id:

1. take one seed fixation at the oracle-supplied yaw/pitch using the unchanged
   generic renderer and stereo front end;
2. if usable selected-object geometry exists, grow with frozen local machinery
   until `no_frontier` or the object watchdog;
3. run the established read-only epistemic audit;
4. only for `no_frontier` + exterior `NEVER_OBSERVED > 0`, permit one bounded
   epistemic handoff and at most one returned local action;
5. freeze the object status and move on.

There is no recursive handoff scheduler and no revisit scheduler in REAL-1.

## Observer seal and evaluator phase

Before full evaluator truth is rendered/opened, export and seal the observer:
per-object geometry, combined point cloud, sparse observer depth/instance
panoramas, fixation history, status table and `observer_complete.json`.

Only after that seal may the evaluator phase generate reference RGB/depth/
instance panoramas and compute coverage/depth-error/purity/efficiency metrics.
Truth may evaluate the observer; it may not repair it.

## RGB-D naming discipline

If the current surfel representation carries no photometric RGB, do not invent
an observer RGB panorama. A reference RGB panorama is an evaluator product. If
Code can construct an RGB mosaic solely from acquired observer images, it may
export it as an explicitly named observer-acquisition mosaic; otherwise the
observer's primary panorama products remain sparse depth/instance/validity.

## Checkpoint / resume

Each completed object gets `object_complete.json`. `--resume` skips completed
objects without rerendering them and continues global step numbering. A sealed
observer must never silently resume into additional control actions.

## Branch discipline

All REAL-1 repair/integration/result work stays on `fullscene-real-1`. `main`
and `fullscene-calibration-1` remain untouched.
