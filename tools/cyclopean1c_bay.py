"""Pure-array bay selection for Cyclopean-1c.

No Blender, truth, scene fixture or controller is known here.  The selector
receives a completed Cyclopean-1b BoundaryAudit and the inherited chart and
chooses one complement cell from the deepest eligible exterior component.
"""
from __future__ import annotations
import math
import numpy as np

import cyclopean1b_boundary as boundary


def _cell_gaze(chart, y: int, x: int) -> tuple[float, float]:
    return (
        float(chart.yaw0_deg + int(x) * chart.grid_deg),
        float(chart.pitch0_deg + int(y) * chart.grid_deg),
    )


def _is_revisit(gaze: tuple[float, float], existing_gazes: list[tuple[float, float]]) -> bool:
    return any(np.allclose(np.asarray(g, float), np.asarray(gaze, float), atol=1e-9)
               for g in existing_gazes)


def select_deep_bay_probe(audit, chart, existing_gazes: list[tuple[float, float]]) -> dict | None:
    """Select one gaze without thresholds or tuned scores.

    Eligible components are EXTERIOR complement components with at least one
    UNOBSERVED shoreline cell.  Components are ordered by the greatest exterior
    border distance reached by those UNOBSERVED shoreline cells.  The probe is
    then the deepest complement cell in the selected component.  Ties are
    resolved geometrically and deterministically, never by a quality threshold.
    """
    eligible = []
    for comp in audit.components:
        if comp["kind"] != "EXTERIOR":
            continue
        cid = int(comp["component_id"])
        umask = (
            audit.shoreline
            & (audit.component_labels == cid)
            & (audit.state_code == boundary.STATE_CODE["UNOBSERVED"])
        )
        ys, xs = np.nonzero(umask)
        if len(ys) == 0:
            continue
        ud = audit.exterior_distance_cells[ys, xs]
        eligible.append({
            "component_id": cid,
            "unobserved_shoreline_cells": int(len(ys)),
            "unobserved_shoreline_max_depth_cells": int(np.max(ud)),
        })
    if not eligible:
        return None
    eligible.sort(key=lambda q: (
        -q["unobserved_shoreline_max_depth_cells"],
        -q["unobserved_shoreline_cells"],
        q["component_id"],
    ))
    chosen = eligible[0]
    cid = int(chosen["component_id"])
    cmask = audit.component_labels == cid
    ys, xs = np.nonzero(cmask & (audit.exterior_distance_cells >= 0))
    if len(ys) == 0:
        raise AssertionError("eligible exterior component has no reachable complement cells")
    dd = audit.exterior_distance_cells[ys, xs]
    # Deterministic ordering: deepest first.  Within a depth plateau, use the
    # cell nearest that plateau's raster centroid; final tie by y/x.
    order_rows = []
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


def _synthetic_audit(physical_only: bool = False):
    raw, support, rr, ev = boundary._synthetic_arrays()
    a = boundary.analyze_boundary(
        raw_support=raw,
        support=support,
        target_range_m=rr,
        evidence=ev,
        grid_deg=.1,
        yaw0_deg=-2.0,
        pitch0_deg=-1.5,
        footprint_cells=1,
        association_radius_m=.012,
    )
    if physical_only:
        ys, xs = np.nonzero(a.shoreline)
        ev.seen_nontarget[ys, xs] = True
        ev.nontarget_range_m[ys, xs] = 3.0
        a = boundary.analyze_boundary(
            raw_support=raw,
            support=support,
            target_range_m=rr,
            evidence=ev,
            grid_deg=.1,
            yaw0_deg=-2.0,
            pitch0_deg=-1.5,
            footprint_cells=1,
            association_radius_m=.012,
        )
    class Chart:
        yaw0_deg = -2.0
        pitch0_deg = -1.5
        grid_deg = .1
    return a, Chart()


def self_test() -> None:
    a, chart = _synthetic_audit()
    p = select_deep_bay_probe(a, chart, [])
    if p is None:
        raise AssertionError("synthetic exterior bay did not produce a probe")
    cid = int(p["component_id"])
    if not a.component_touches_border[cid]:
        raise AssertionError("selected component is not exterior")
    if int(p["probe_border_distance_cells"]) != int(np.max(a.exterior_distance_cells[a.component_labels == cid])):
        raise AssertionError("probe is not at deepest exterior complement distance")
    first = tuple(p["probe_gaze_deg"])
    p2 = select_deep_bay_probe(a, chart, [first])
    if p2 is None or tuple(p2["probe_gaze_deg"]) == first:
        raise AssertionError("visited deepest cell did not trigger deterministic fallback")
    b, chart2 = _synthetic_audit(physical_only=True)
    if select_deep_bay_probe(b, chart2, []) is not None:
        raise AssertionError("physical-only exterior shoreline incorrectly produced a bay probe")
    print("[cyclopean1c-bay] PASS exterior_deepest=true physical_excluded=true revisit_fallback=true one_probe=true")


if __name__ == "__main__":
    self_test()
