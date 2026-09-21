"""Pure-array epistemic gaze selection for Cyclopean-1e.

No Blender, truth, scene fixture or controller is known here.  The selector
receives the final spherical shoreline, Cyclopean-1d refined state raster and
inherited exterior-distance field, and chooses one EXTERIOR NEVER_OBSERVED
shoreline cell.  Seen-but-unmeasured cells are not eligible.
"""
from __future__ import annotations
import numpy as np


def _cell_gaze(chart, y: int, x: int) -> tuple[float, float]:
    return (
        float(chart.yaw0_deg + int(x) * chart.grid_deg),
        float(chart.pitch0_deg + int(y) * chart.grid_deg),
    )


def _is_revisit(gaze: tuple[float, float], existing_gazes: list[tuple[float, float]]) -> bool:
    return any(
        np.allclose(np.asarray(g, float), np.asarray(gaze, float), atol=1e-9)
        for g in existing_gazes
    )


def select_epistemic_probe(
    *,
    shoreline: np.ndarray,
    component_labels: np.ndarray,
    components: list[dict],
    exterior_distance_cells: np.ndarray,
    refined_state: np.ndarray,
    never_observed_code: int,
    chart,
    existing_gazes: list[tuple[float, float]],
) -> dict | None:
    """Choose one deepest unvisited EXTERIOR NEVER_OBSERVED shoreline cell.

    No threshold or tuned score is used.  Exterior components are ranked by the
    maximum inherited border distance reached by their NEVER_OBSERVED shoreline,
    then by the number of such cells, then component id.  Within the selected
    component, candidate cells are ordered deepest first.  A depth plateau is
    ordered by distance to its raster centroid, then y/x.  Revisited gazes are
    skipped using that same deterministic order.
    """
    shoreline = np.asarray(shoreline, bool)
    labels = np.asarray(component_labels)
    distance = np.asarray(exterior_distance_cells)
    refined = np.asarray(refined_state)
    if not (shoreline.shape == labels.shape == distance.shape == refined.shape):
        raise ValueError("selector arrays must share one chart shape")

    eligible = []
    for comp in components:
        if comp.get("kind") != "EXTERIOR":
            continue
        cid = int(comp["component_id"])
        mask = shoreline & (labels == cid) & (refined == int(never_observed_code))
        ys, xs = np.nonzero(mask)
        if len(ys) == 0:
            continue
        dd = distance[ys, xs]
        if np.any(dd < 0):
            raise AssertionError("EXTERIOR NEVER_OBSERVED shoreline has unreachable border distance")
        eligible.append({
            "component_id": cid,
            "never_observed_shoreline_cells": int(len(ys)),
            "never_observed_max_depth_cells": int(np.max(dd)),
        })

    if not eligible:
        return None

    eligible.sort(key=lambda q: (
        -q["never_observed_max_depth_cells"],
        -q["never_observed_shoreline_cells"],
        q["component_id"],
    ))
    chosen = eligible[0]
    cid = int(chosen["component_id"])
    mask = shoreline & (labels == cid) & (refined == int(never_observed_code))
    ys, xs = np.nonzero(mask)
    dd = distance[ys, xs]

    order_rows: list[tuple[int, int, int]] = []
    for d in sorted(set(int(v) for v in dd), reverse=True):
        take = np.nonzero(dd == d)[0]
        cy = float(np.mean(ys[take])); cx = float(np.mean(xs[take]))
        local = sorted(
            ((float((ys[k]-cy)**2 + (xs[k]-cx)**2), int(ys[k]), int(xs[k])) for k in take),
            key=lambda q: (q[0], q[1], q[2]),
        )
        order_rows.extend((d, y, x) for _, y, x in local)

    fallback_rank = 0
    for d, y, x in order_rows:
        gaze = _cell_gaze(chart, y, x)
        if _is_revisit(gaze, existing_gazes):
            fallback_rank += 1
            continue
        return {
            **chosen,
            "probe_cell_y": int(y),
            "probe_cell_x": int(x),
            "probe_gaze_deg": [float(gaze[0]), float(gaze[1])],
            "probe_border_distance_cells": int(d),
            "revisit_fallback_rank": int(fallback_rank),
            "eligible_component_count": int(len(eligible)),
        }
    return None


def self_test() -> None:
    h, w = 8, 10
    shoreline = np.zeros((h, w), bool)
    labels = np.full((h, w), -1, np.int32)
    distance = np.full((h, w), -1, np.int32)
    refined = np.zeros((h, w), np.uint8)
    NEVER = 1
    NO_DEPTH = 2

    # Exterior component 0: two NEVER_OBSERVED candidates at depths 7 and 4,
    # plus a deeper seen-but-no-depth cell that must be excluded.
    for y, x, d, state in ((3,7,7,NEVER), (3,5,4,NEVER), (3,8,9,NO_DEPTH)):
        shoreline[y, x] = True; labels[y, x] = 0; distance[y, x] = d; refined[y, x] = state
    # Internal component 1: a deeper NEVER_OBSERVED cell that must be excluded.
    shoreline[5,5] = True; labels[5,5] = 1; distance[5,5] = -1; refined[5,5] = NEVER
    components = [
        {"component_id": 0, "kind": "EXTERIOR"},
        {"component_id": 1, "kind": "INTERNAL"},
    ]
    class Chart:
        yaw0_deg = -1.0
        pitch0_deg = -1.0
        grid_deg = 0.1

    p = select_epistemic_probe(
        shoreline=shoreline,
        component_labels=labels,
        components=components,
        exterior_distance_cells=distance,
        refined_state=refined,
        never_observed_code=NEVER,
        chart=Chart(),
        existing_gazes=[],
    )
    if p is None or p["probe_cell_y"] != 3 or p["probe_cell_x"] != 7:
        raise AssertionError("selector did not choose deepest exterior NEVER_OBSERVED cell")
    first = tuple(p["probe_gaze_deg"])
    p2 = select_epistemic_probe(
        shoreline=shoreline,
        component_labels=labels,
        components=components,
        exterior_distance_cells=distance,
        refined_state=refined,
        never_observed_code=NEVER,
        chart=Chart(),
        existing_gazes=[first],
    )
    if p2 is None or p2["probe_cell_x"] != 5:
        raise AssertionError("visited deepest epistemic cell did not trigger fallback")
    refined_no_never = refined.copy(); refined_no_never[refined_no_never == NEVER] = NO_DEPTH
    p3 = select_epistemic_probe(
        shoreline=shoreline,
        component_labels=labels,
        components=components,
        exterior_distance_cells=distance,
        refined_state=refined_no_never,
        never_observed_code=NEVER,
        chart=Chart(),
        existing_gazes=[],
    )
    if p3 is not None:
        raise AssertionError("seen-but-no-depth shoreline incorrectly became a gaze candidate")
    print("[cyclopean1e-gaze] PASS never_observed_only=true internal_excluded=true no_depth_excluded=true exterior_deepest=true revisit_fallback=true one_probe=true")


if __name__ == "__main__":
    self_test()
