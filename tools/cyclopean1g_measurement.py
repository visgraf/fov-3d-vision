"""Pure selector and outcome helpers for Cyclopean-1g.

No Blender, truth, scene fixture, FSG6f controller or stereo code is known here.
The selector receives an already-refined cyclopean shoreline and chooses one
unvisited INTERNAL OBSERVED_TARGET_NO_DEPTH cell near the dominant residue's
chart centroid.  The outcome helper only distinguishes whether valid target
stereo depth was recovered for any pre-probe residue cell.
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


def select_remeasurement_probe(
    *,
    shoreline: np.ndarray,
    component_labels: np.ndarray,
    components: list[dict],
    refined_state: np.ndarray,
    observed_target_no_depth_code: int,
    chart,
    existing_gazes: list[tuple[float, float]],
) -> dict | None:
    """Choose one centroid-near cell in the dominant INTERNAL no-depth residue.

    Components are ordered by number of OBSERVED_TARGET_NO_DEPTH shoreline
    cells, then by total component cell count when available, then component id.
    Within the selected component, cells are ordered by squared raster distance
    to the no-depth-cell centroid, then y/x.  Revisited gazes are skipped in that
    same deterministic order.  There is no threshold or tuned score.
    """
    shoreline = np.asarray(shoreline, bool)
    labels = np.asarray(component_labels)
    refined = np.asarray(refined_state)
    if not (shoreline.shape == labels.shape == refined.shape):
        raise ValueError("selector arrays must share one chart shape")

    eligible: list[dict] = []
    for comp in components:
        if comp.get("kind") != "INTERNAL":
            continue
        cid = int(comp["component_id"])
        mask = shoreline & (labels == cid) & (refined == int(observed_target_no_depth_code))
        ys, xs = np.nonzero(mask)
        if len(ys) == 0:
            continue
        eligible.append({
            "component_id": cid,
            "observed_target_no_depth_cells": int(len(ys)),
            "component_cell_count": int(comp.get("cell_count", len(ys))),
        })

    if not eligible:
        return None
    eligible.sort(key=lambda q: (
        -q["observed_target_no_depth_cells"],
        -q["component_cell_count"],
        q["component_id"],
    ))
    chosen = eligible[0]
    cid = int(chosen["component_id"])
    mask = shoreline & (labels == cid) & (refined == int(observed_target_no_depth_code))
    ys, xs = np.nonzero(mask)
    cy = float(np.mean(ys)); cx = float(np.mean(xs))
    order = sorted(
        ((float((int(y)-cy)**2 + (int(x)-cx)**2), int(y), int(x)) for y, x in zip(ys, xs)),
        key=lambda q: (q[0], q[1], q[2]),
    )
    fallback_rank = 0
    for d2, y, x in order:
        gaze = _cell_gaze(chart, y, x)
        if _is_revisit(gaze, existing_gazes):
            fallback_rank += 1
            continue
        return {
            **chosen,
            "probe_cell_y": int(y),
            "probe_cell_x": int(x),
            "probe_gaze_deg": [float(gaze[0]), float(gaze[1])],
            "component_centroid_cell": [float(cy), float(cx)],
            "probe_centroid_distance_sq_cells": float(d2),
            "revisit_fallback_rank": int(fallback_rank),
            "eligible_component_count": int(len(eligible)),
        }
    return None


def classify_measurement_outcome(*, recovered_valid_target_cells: int) -> str:
    return "DEPTH_RECOVERED" if int(recovered_valid_target_cells) > 0 else "DEPTH_STILL_ABSENT"


def self_test() -> None:
    h, w = 9, 11
    shoreline = np.zeros((h, w), bool)
    labels = np.full((h, w), -1, np.int32)
    refined = np.zeros((h, w), np.uint8)
    NO_DEPTH = 2
    NEVER = 1

    # Dominant INTERNAL component 2: three no-depth cells.  Its centroid-near
    # cell is (4,7).  An exterior no-depth cell and an internal NEVER cell must
    # both remain ineligible.
    for y, x in ((4,6), (4,7), (5,7)):
        shoreline[y, x] = True; labels[y, x] = 2; refined[y, x] = NO_DEPTH
    shoreline[2,2] = True; labels[2,2] = 0; refined[2,2] = NO_DEPTH
    shoreline[6,3] = True; labels[6,3] = 1; refined[6,3] = NEVER
    components = [
        {"component_id": 0, "kind": "EXTERIOR", "cell_count": 50},
        {"component_id": 1, "kind": "INTERNAL", "cell_count": 1},
        {"component_id": 2, "kind": "INTERNAL", "cell_count": 9},
    ]

    class Chart:
        yaw0_deg = -1.0
        pitch0_deg = -1.0
        grid_deg = 0.1

    p = select_remeasurement_probe(
        shoreline=shoreline,
        component_labels=labels,
        components=components,
        refined_state=refined,
        observed_target_no_depth_code=NO_DEPTH,
        chart=Chart(),
        existing_gazes=[],
    )
    if p is None or p["component_id"] != 2 or (p["probe_cell_y"], p["probe_cell_x"]) != (4,7):
        raise AssertionError("selector did not choose dominant INTERNAL no-depth residue centre")
    p2 = select_remeasurement_probe(
        shoreline=shoreline,
        component_labels=labels,
        components=components,
        refined_state=refined,
        observed_target_no_depth_code=NO_DEPTH,
        chart=Chart(),
        existing_gazes=[tuple(p["probe_gaze_deg"])],
    )
    if p2 is None or p2["revisit_fallback_rank"] != 1:
        raise AssertionError("centroid revisit did not trigger deterministic fallback")
    if classify_measurement_outcome(recovered_valid_target_cells=3) != "DEPTH_RECOVERED":
        raise AssertionError("recovered depth outcome not recognized")
    if classify_measurement_outcome(recovered_valid_target_cells=0) != "DEPTH_STILL_ABSENT":
        raise AssertionError("absent depth outcome not recognized")
    print("[cyclopean1g-measurement] PASS internal_no_depth_only=true centroid_recentering=true revisit_fallback=true binary_outcome=true one_probe=true")


if __name__ == "__main__":
    self_test()
