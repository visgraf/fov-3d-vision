# Classroom-Oracle-2: Boundary Ablation

## Question

Classroom-Oracle-1 established that with essentially perfect local stereo the active controller reconstructs the usable interior of the Classroom well, while most residual misses concentrate near the controller's own yaw +/-25 deg, pitch +/-20 deg boundary.

Classroom-Oracle-2 changes exactly one scientific variable:

```text
Oracle-1  yaw +/-25 deg, pitch +/-20 deg
Oracle-2  yaw +/-35 deg, pitch +/-30 deg
```

The experiment asks whether the Oracle-1 boundary deficit was caused by a field that was simply too tight, or whether the frontier / Cyclopean shoreline mechanism still leaves analogous holes after the old boundary becomes interior.

## Frozen quantities

The following are unchanged from the completed Classroom-Oracle-1 run at result commit `f9fb196`:

- Classroom scene and fixed head;
- the exact 25 target instance IDs;
- the exact Oracle-1 seed gaze for every target;
- full render profile and binocular sensor;
- perfect local oracle measurement and half-occlusion semantics;
- no SGBM 0.75-4.5 m range bound;
- FSG6f decision logic;
- Cyclopean NEVER_OBSERVED + EXTERIOR shoreline handoff;
- 12 mm association / hash-cell fusion;
- 24-fixation engineering watchdog;
- no foreground/background decomposition;
- no quality PASS threshold.

New objects that become visible only because of the wider domain are retained in evaluation truth but are not added to the target set.

## Truth isolation

The Blender bootstrap creates dense first-hit samples for the widened domain, but these are written under `bootstrap/evaluation_only/` and are not opened by the control loop.  The original-domain dense truth is copied there only for post-run comparison.

Controller-visible bootstrap information remains exactly one Oracle-1 seed per one of the original 25 targets.

## Evaluation

Evaluation is performed in two scopes.

### A. Original domain

Re-evaluate the Oracle-2 final maps on the exact same +/-25 deg, +/-20 deg reachable samples used by Oracle-1.

Measure:

- Oracle-1 coverage on those samples;
- Oracle-2 coverage on those same samples;
- fraction of Oracle-1 misses recovered by Oracle-2;
- baseline hits that regress in Oracle-2;
- coverage versus distance from the old boundary.

### B. Widened domain

Evaluate the same 25 target maps on reachable samples in +/-35 deg, +/-30 deg.

Measure:

- total wide-domain coverage;
- coverage versus distance from the new boundary;
- whether the residual deficit migrates outward to the new boundary;
- per-object fixation count and coverage.

There is no numerical scientific PASS threshold.  The shape of the result is the experiment.

## Interpretation

Three outcomes are especially diagnostic:

1. **Old holes are recovered.** The original angular extent was limiting coverage.
2. **Old holes remain despite extra angular room.** The next suspect is frontier / shoreline eligibility rather than stereo or fusion.
3. **Old holes are recovered but a new edge ring appears at +/-35 deg, +/-30 deg.** The residual is a general finite-domain boundary effect.

No policy constant is to be tuned in response to the result.

## Demo deliverable

After evaluation, generate the observational demo with `classroom_oracle2_demo.py`.

The demo must show the experiment as a sequence, not merely a final cloud:

```text
Blender reference
    -> selected object / fixation
    -> left + right tangent observation
    -> cyclopean angular state
    -> surface growth
    -> persistent scene reconstruction
    -> next controller fixation
    -> final panoramas / point clouds / reference comparison
```

The preferred video is a synchronized four-view display:

1. Blender reference / target / gaze;
2. current binocular observation;
3. evolving cyclopean coverage state;
4. accumulating 3-D reconstruction.

Demo generation occurs only after control and cannot feed information back into the experiment.
