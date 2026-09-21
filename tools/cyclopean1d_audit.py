"""Read-only observation-versus-measurement audit for completed Cyclopean-1c.

No acquisition is launched.  The final 1c shoreline is rebuilt on the inherited
chart.  Only cells whose frozen Cyclopean-1b state is UNOBSERVED are refined by
asking whether a continuation point at the already-existing local target range
was present in completed target imagery and whether frozen stereo had valid
depth there.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

import cyclopean1a_topology as topo1a
import cyclopean1a_probe as probe1a
import cyclopean1b_audit as audit1b
import cyclopean1b_boundary as boundary1b
import cyclopean1c_probe as probe1c
import cyclopean1c_public as parent_public
import cyclopean1d_public as public
import cyclopean1d_epistemic as epi
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg_stereo import rectification
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _validate_parent(parent: Path) -> dict:
    m = json.loads((parent / "prediction_manifest.json").read_text())
    if m.get("schema") != "Cyclopean1c-bay-probe-v1":
        raise AssertionError("Cyclopean-1d requires a completed Cyclopean-1c parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("Cyclopean-1c public digest mismatch")
    if int(m.get("seed", -1)) != 2111 or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("fixed-head/static-scene invariant broken")
    if int(m.get("added_fixations", -1)) != 1 or int(m.get("parent_fixations_rerendered", -1)) != 0:
        raise AssertionError("Cyclopean-1c acquisition contract mismatch")
    return m


def _load_saved_observation(calibration_path: Path, patch_path: Path, label: str) -> dict:
    c = json.loads(calibration_path.read_text())
    r = rectification(c)
    with np.load(patch_path, allow_pickle=False) as z:
        ids = z["oracle_instance_id"].copy()
        valid = z["valid"].astype(bool, copy=True)
        support = z["raw_support_L"].astype(bool, copy=True)
    if ids.shape != valid.shape or ids.shape != support.shape:
        raise AssertionError(f"saved observation shape mismatch: {label}")
    return {"label": label, "calibration": c, "rectification": r,
            "instance_id": ids, "valid": valid, "raw_support_L": support}


def _observation_history(parent1c: Path, pm1c: dict) -> tuple[list[dict], dict]:
    parent1b = Path(pm1c["parent_record"])
    pm1b = json.loads((parent1b / "prediction_manifest.json").read_text())
    parent1a = Path(pm1b["parent_record"])
    pm1a = json.loads((parent1a / "prediction_manifest.json").read_text())
    rc2b = Path(pm1a["parent_record"])
    pm2b = probe1a._validate_parent(rc2b)
    reality1 = Path(pm2b["parent_record"])
    n0 = int(pm2b["parent_fixation_count"])
    total = len(pm2b["fixation_gazes_deg"])
    obs: list[dict] = []
    for step in range(total):
        if step < n0:
            base = reality1
        else:
            base = rc2b
        cal = base / "acquisitions" / f"fix_{step:02d}" / f"fix_{step:02d}" / "calibration.json"
        patch = base / "patches" / f"fix_{step:02d}.npz"
        obs.append(_load_saved_observation(cal, patch, f"fix_{step:02d}"))

    # Seed 2111 had no 1a acquisition in the measured parent.  If history ever
    # changes, include it rather than silently losing an observation.
    if pm1a.get("probe_result", {}).get("probe_taken"):
        dirs = sorted((parent1a / "acquisition").glob("fix_*"))
        if len(dirs) != 1:
            raise AssertionError("unexpected Cyclopean-1a probe acquisition layout")
        obs.append(_load_saved_observation(dirs[0] / "calibration.json", parent1a / "probe_patch.npz", dirs[0].name))

    dirs1c = sorted((parent1c / "acquisition").glob("fix_*"))
    if len(dirs1c) != 1:
        raise AssertionError("Cyclopean-1c must contain exactly one probe acquisition")
    obs.append(_load_saved_observation(dirs1c[0] / "calibration.json", parent1c / "probe_patch.npz", dirs1c[0].name))
    return obs, {"reality1": str(reality1), "reality2b": str(rc2b),
                 "cyclopean1a": str(parent1a), "cyclopean1b": str(parent1b)}


def _rebuild_final_boundary(parent1c: Path, pm1c: dict):
    parent1b = Path(pm1c["parent_record"])
    pm1b = probe1c._validate_parent(parent1b)
    parent1a, pm1a, _sm1a, chart, fc, fd, evidence, _rb, _sb, _rrb, _ab = probe1c._rebuild(parent1b, pm1b)
    dirs = sorted((parent1c / "acquisition").glob("fix_*"))
    if len(dirs) != 1:
        raise AssertionError("Cyclopean-1c probe acquisition not unique")
    c, obs = hdr.read_observation(dirs[0])
    rec, _, _ = compute_once(c, obs)
    topo1a.add_observation(evidence, chart, rec["xyz_h"], rec["instance_id"], rec["valid"], public.OBJECT_ID)
    sm = load_map(parent1c / "surface_map.npz")
    raw, support, target_range = topo1a.rasterize_target(sm.xyz_h, chart, fc)
    ev = boundary1b.EvidenceArrays(evidence.seen_target, evidence.seen_nontarget,
                                   evidence.target_range_m, evidence.nontarget_range_m)
    audit = boundary1b.analyze_boundary(
        raw_support=raw, support=support, target_range_m=target_range, evidence=ev,
        grid_deg=chart.grid_deg, yaw0_deg=chart.yaw0_deg, pitch0_deg=chart.pitch0_deg,
        footprint_cells=fc, association_radius_m=float(public.FUSION["association_radius_m"]),
    )
    return parent1a, pm1a, sm, chart, fc, fd, raw, support, audit


def _cell_point(chart, y: int, x: int, rho: float) -> np.ndarray:
    yaw = chart.yaw0_deg + x * chart.grid_deg
    pitch = chart.pitch0_deg + y * chart.grid_deg
    return topo1a.angles_to_dir(float(yaw), float(pitch)) * float(rho)


def _components(mask: np.ndarray) -> list[np.ndarray]:
    m = np.asarray(mask, bool)
    h, w = m.shape
    seen = np.zeros_like(m)
    out = []
    nbr = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    for y0, x0 in zip(*np.nonzero(m)):
        if seen[y0, x0]:
            continue
        stack = [(int(y0), int(x0))]; seen[y0, x0] = True; cells = []
        while stack:
            y, x = stack.pop(); cells.append((y, x))
            for dy, dx in nbr:
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and m[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; stack.append((yy, xx))
        out.append(np.asarray(cells, np.int32))
    return out


def _refine_unobserved(chart, audit, observations: list[dict]) -> tuple[np.ndarray, dict[tuple[int,int], epi.ProjectedEvidence]]:
    refined = np.zeros(audit.shoreline.shape, np.uint8)
    evidence_by_cell: dict[tuple[int,int], epi.ProjectedEvidence] = {}
    unobs_code = boundary1b.STATE_CODE["UNOBSERVED"]
    for y, x in zip(*np.nonzero(audit.shoreline & (audit.state_code == unobs_code))):
        rho = float(audit.local_target_range_m[y, x])
        if not np.isfinite(rho) or rho <= 0:
            refined[y, x] = epi.STATE_CODE["NO_RANGE_REFERENCE"]
            evidence_by_cell[(int(y), int(x))] = epi.ProjectedEvidence()
            continue
        point = _cell_point(chart, int(y), int(x), rho)[None, :]
        total = epi.ProjectedEvidence()
        for ob in observations:
            e = epi.sample_projected_evidence(
                ob["calibration"], ob["rectification"], ob["instance_id"], ob["valid"],
                ob["raw_support_L"], point, public.OBJECT_ID,
            )[0]
            total = epi.add_evidence(total, e)
        state = epi.classify_counts(total, True)
        refined[y, x] = epi.STATE_CODE[state]
        evidence_by_cell[(int(y), int(x))] = total
    return refined, evidence_by_cell


def _arc_rows(chart, audit, refined: np.ndarray, cell_ev: dict[tuple[int,int], epi.ProjectedEvidence]) -> list[dict]:
    rows = []
    arc_id = 0
    for code, name in epi.CODE_STATE.items():
        for comp in audit.components:
            cid = int(comp["component_id"])
            mask = audit.shoreline & (audit.component_labels == cid) & (refined == code)
            for cells in _components(mask):
                if len(cells) == 0:
                    continue
                yaw = chart.yaw0_deg + cells[:,1] * chart.grid_deg
                pitch = chart.pitch0_deg + cells[:,0] * chart.grid_deg
                totals = epi.ProjectedEvidence()
                for y, x in cells:
                    totals = epi.add_evidence(totals, cell_ev[(int(y), int(x))])
                d = audit.exterior_distance_cells[cells[:,0], cells[:,1]]
                kind = comp["kind"]
                rows.append({
                    "arc_id": arc_id,
                    "component_id": cid,
                    "component_kind": kind,
                    "state": name,
                    "cell_count": int(len(cells)),
                    "centroid_yaw_deg": float(np.mean(yaw)),
                    "centroid_pitch_deg": float(np.mean(pitch)),
                    "target_seen_samples": totals.target_seen,
                    "target_depth_valid_samples": totals.target_depth_valid,
                    "nontarget_seen_samples": totals.nontarget_seen,
                    "nontarget_depth_valid_samples": totals.nontarget_depth_valid,
                    "supported_projection_samples": totals.supported_projections,
                    "border_distance_cells_max": int(np.max(d)) if kind == "EXTERIOR" else None,
                })
                arc_id += 1
    rows.sort(key=lambda r: (0 if r["component_kind"] == "EXTERIOR" else 1,
                             -int(r["border_distance_cells_max"] or -1),
                             -r["cell_count"], r["state"]))
    return rows


def _write_visual(path: Path, support: np.ndarray, audit, refined: np.ndarray) -> None:
    h, w = support.shape
    im = np.full((h, w, 3), 245, np.uint8)
    im[support] = (150, 150, 150)
    # Preserve existing non-UNOBSERVED boundary semantics.
    im[audit.state_code == boundary1b.STATE_CODE["PHYSICAL_DEPTH_BREAK"]] = (70, 125, 220)
    im[audit.state_code == boundary1b.STATE_CODE["AMBIGUOUS"]] = (175, 105, 185)
    colours = {
        "NEVER_OBSERVED": (235, 80, 70),
        "OBSERVED_TARGET_NO_DEPTH": (245, 155, 55),
        "OBSERVED_TARGET_WITH_DEPTH": (235, 205, 55),
        "OBSERVED_NONTARGET_ONLY": (75, 190, 190),
        "MIXED_OBSERVATION": (220, 95, 170),
        "NO_RANGE_REFERENCE": (100, 100, 100),
    }
    for name, code in epi.STATE_CODE.items():
        im[refined == code] = colours[name]
    Image.fromarray(np.flipud(im)).resize((max(1, w*3), max(1, h*3)), Image.Resampling.NEAREST).save(path)


def execute(args) -> dict:
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()
    pm = _validate_parent(args.parent)
    pinned = {n: _sha256(args.parent / n) for n in (
        "prediction_manifest.json", "surface_map.npz", "probe_patch.npz", "shoreline_after.png")}
    parent1a, pm1a, sm, chart, fc, fd, raw, support, audit = _rebuild_final_boundary(args.parent, pm)
    observations, ancestry = _observation_history(args.parent, pm)
    refined, cell_ev = _refine_unobserved(chart, audit, observations)
    arcs = _arc_rows(chart, audit, refined, cell_ev)
    counts = {name: int((refined == code).sum()) for name, code in epi.STATE_CODE.items()}
    ext_counts = {name: 0 for name in epi.STATE_CODE}
    int_counts = {name: 0 for name in epi.STATE_CODE}
    for r in arcs:
        (ext_counts if r["component_kind"] == "EXTERIOR" else int_counts)[r["state"]] += r["cell_count"]
    report = {
        "seed": int(pm["seed"]),
        "profile": str(pm["profile"]),
        "observation_count": len(observations),
        "observation_labels": [o["label"] for o in observations],
        "chart": {"yaw0_deg": chart.yaw0_deg, "pitch0_deg": chart.pitch0_deg,
                  "grid_deg": chart.grid_deg, "width": chart.width, "height": chart.height},
        "footprint_cells": fc,
        "footprint_radius_deg": fd,
        "map_points": int(len(sm.xyz_h)),
        "shoreline_cells": int(audit.shoreline.sum()),
        "base_unobserved_shoreline_cells": int((audit.state_code == boundary1b.STATE_CODE["UNOBSERVED"]).sum()),
        "refined_unobserved_cells_by_state": counts,
        "exterior_refined_cells_by_state": ext_counts,
        "internal_refined_cells_by_state": int_counts,
        "refined_arcs": arcs,
        "ancestry": ancestry,
    }
    json_write(args.out / "observation_measurement_report.json", report)
    _write_visual(args.out / "epistemic_shoreline.png", support, audit, refined)
    after = {n: _sha256(args.parent / n) for n in pinned}
    if after != pinned:
        raise AssertionError("Cyclopean-1c parent changed during read-only audit")
    manifest = {
        "schema": "Cyclopean1d-observation-measurement-audit-v1",
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "parent_hashes": pinned,
        "seed": int(pm["seed"]),
        "profile": str(pm["profile"]),
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "acquisitions_added": 0,
        "parent_files_modified": False,
        "observation_count": len(observations),
        "summary": {
            "base_unobserved_shoreline_cells": report["base_unobserved_shoreline_cells"],
            "refined_unobserved_cells_by_state": counts,
            "exterior_refined_cells_by_state": ext_counts,
            "internal_refined_cells_by_state": int_counts,
        },
        "report": "observation_measurement_report.json",
        "visual": "epistemic_shoreline.png",
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    print("[cyclopean1d-audit] COMPLETE", json.dumps({"seed": manifest["seed"], **manifest["summary"]}, sort_keys=True), flush=True)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    execute(ap.parse_args())


if __name__ == "__main__":
    main()
