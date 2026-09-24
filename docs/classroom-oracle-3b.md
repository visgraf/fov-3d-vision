# Classroom-Oracle-3b: Gap Anatomy

## Question

Classroom-Oracle-3 established that the dominant residual error is not rejected by the exterior-only or never-observed clauses. **98.75% of all reachable-but-uncovered samples fail earlier because they are not on the current one-ring Cyclopean shoreline**, and 94.80% are `COMPLEMENT_NONSHORELINE`.

Oracle-3b asks:

> **What is the geometry and observation history of the missing surface on the other side of that gap?**

The purpose is to distinguish two qualitatively different possibilities before changing control behavior:

1. the detached surface lies only a few Cyclopean expansion rings beyond current support, suggesting that the one-ring shoreline is simply too local;
2. the detached surface forms genuinely remote components, suggesting that a true global re-find mechanism is needed rather than a slightly thicker shoreline.

It also separates genuinely unseen detached surface from surface that the eyes already imaged but the persistent map does not represent.

## Scientific contract

Oracle-3b is **post-hoc and read-only**. It performs no controller replay, no gaze selection, no Blender launch, no acquisition, no fusion, no domain change and no policy change. It consumes the completed Oracle-3 audit and the frozen Oracle-1 reachable-surface reference.

The focus set is inherited from Oracle-3 (`focus_instance_ids`), which is itself the six largest Oracle-1 miss counts from Oracle-2 Scope A. No object IDs are chosen by hand here.

## Core measurement: support-expansion ring depth

On the frozen 0.1-degree Cyclopean chart:

- mapped angular support has ring depth 0;
- the current one-ring shoreline is at ring depth 1;
- a detached miss at ring depth `k` would require `k` successive 8-connected support dilations before it became adjacent to support.

This is measured with the Chebyshev (`DIST_C`) distance transform of the final support mask. It is **not** a proposed new eligibility rule.

Oracle-3b reports both this exact ring count and Euclidean angular distance in degrees.

## Connected components

A subtlety matters: Oracle-1 reachable truth is sampled at its own angular lattice (0.25 degrees in the completed experiment), while the Cyclopean state raster is 0.1 degrees. Running connectivity directly on the 0.1-degree raster would spuriously fragment truth samples that are legitimately adjacent on the reference lattice.

Therefore connected missed-surface components are defined on the **frozen reachable-sample angular lattice inferred from the reference file**, using 8-connectivity there. The finer Cyclopean raster is used only to read support distance and observation state.

For every disconnected component the audit records:

- truth sample count and unique reference cells;
- angular centroid, span and bounding box;
- min/median/p90/max support-ring depth;
- min/median/p90/max angular distance to support and shoreline;
- nearest completed fixation distance;
- saved observation-state composition;
- fractions genuinely `NEVER_OBSERVED` versus target-seen.

The aggregate `halo_reach_curve` reports the cumulative fraction of detached misses that would become adjacent after `k` geometric support-expansion rings. It is descriptive only; no `k` is selected as a controller parameter.

## Demo

The required demo is also post-hoc. For each of the six focus objects it presents four synchronized diagnostic panels:

1. final support / current shoreline / detached misses;
2. support-expansion ring depth;
3. connected missed-surface components;
4. saved observation-history state on those misses.

It writes `Demo.md`, per-object PNGs, an overview contact sheet and an MP4 when the local OpenCV backend can encode it.

## What Oracle-3b does not do

It does not decide between a thicker halo and a global re-find mechanism. It measures the gap anatomy so that the next behavior-changing experiment can alter exactly one justified mechanism rather than guessing.
