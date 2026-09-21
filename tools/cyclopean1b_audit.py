"""Audit spherical boundary semantics on a completed Cyclopean-1a record.

Read-only host-side analysis.  No Blender process is launched and no fixation is
added.  The exact Cyclopean-1a chart is reconstructed from map_before.npz; the
final surface_map.npz supplies current target support; completed prediction-side
observations supply shoreline evidence.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

import cyclopean1a_public as parent_public
import cyclopean1a_topology as topo1a
import cyclopean1a_probe as probe1a
import cyclopean1b_public as public
import cyclopean1b_boundary as boundary
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg3_surface_map import load_map
from fsg_geometry import json_write


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _validate_parent(record: Path) -> dict:
    m = json.loads((record / "prediction_manifest.json").read_text())
    if m.get("schema") != "Cyclopean1a-probe-v1":
        raise AssertionError("Cyclopean-1b requires a completed Cyclopean-1a record")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("Cyclopean-1a public digest mismatch")
    if m.get("truth_opened") is not False or not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("Cyclopean-1a integrity contract broken")
    if int(m.get("parent_fixations_rerendered", -1)) != 0:
        raise AssertionError("Cyclopean-1a parent rerendered fixations")
    if int(m.get("added_fixations", -1)) not in (0, 1):
        raise AssertionError("Cyclopean-1a added-fixation count outside contract")
    if int(m.get("seed")) not in public.SEEDS:
        raise AssertionError("parent seed outside Cyclopean-1b schedule")
    return m


def _evidence(record: Path, pm1a: dict, chart: topo1a.Chart) -> topo1a.Evidence:
    rc2b = Path(pm1a["parent_record"])
    pm2b = probe1a._validate_parent(rc2b)
    e = probe1a._evidence_from_parent(rc2b, pm2b, chart)
    pr = pm1a.get("probe_result", {})
    if pr.get("probe_taken"):
        step = len(pm2b["fixation_gazes_deg"])
        case = record / "acquisition" / f"fix_{step:02d}"
        if not case.exists():
            raise FileNotFoundError(f"missing Cyclopean-1a probe acquisition: {case}")
        c, obs = hdr.read_observation(case)
        rec, _, _ = compute_once(c, obs)
        topo1a.add_observation(e, chart, rec["xyz_h"], rec["instance_id"], rec["valid"], public.OBJECT_ID)
    return e


def _write_visual(path: Path, support: np.ndarray, audit: boundary.BoundaryAudit) -> None:
    h, w = support.shape
    im = np.full((h, w, 3), 245, np.uint8)
    im[support] = (150, 150, 150)
    # Tint internal complement components so lakes and exterior water remain distinct.
    for cid, touches in audit.component_touches_border.items():
        if not touches:
            im[audit.component_labels == cid] = (250, 225, 215)
    colours = {
        "UNOBSERVED": (235, 80, 70),
        "TARGET_CONTINUATION": (240, 170, 55),
        "PHYSICAL_DEPTH_BREAK": (70, 125, 220),
        "AMBIGUOUS": (175, 105, 185),
    }
    for name, code in boundary.STATE_CODE.items():
        im[audit.state_code == code] = colours[name]
    Image.fromarray(np.flipud(im)).resize((max(1, w*3), max(1, h*3)), Image.Resampling.NEAREST).save(path)


def _summary(audit: boundary.BoundaryAudit) -> dict:
    states = {name: 0 for name in boundary.STATE_CODE}
    exterior = {name: 0 for name in boundary.STATE_CODE}
    internal = {name: 0 for name in boundary.STATE_CODE}
    for a in audit.arcs:
        states[a["state"]] += 1
        (exterior if a["component_kind"] == "EXTERIOR" else internal)[a["state"]] += 1
    ext_arcs = [a for a in audit.arcs if a["component_kind"] == "EXTERIOR"]
    return {
        "arc_count": len(audit.arcs),
        "arcs_by_state": states,
        "exterior_arcs_by_state": exterior,
        "internal_arcs_by_state": internal,
        "max_exterior_border_distance_cells": max((a["border_distance_cells_max"] for a in ext_arcs), default=None),
    }


def execute(args) -> dict:
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()
    pm = _validate_parent(args.parent)
    profile = str(pm["profile"])
    seed = int(pm["seed"])

    parent_hash_before = {n: _sha256(args.parent / n) for n in ("prediction_manifest.json", "map_before.npz", "surface_map.npz")}
    before_map = load_map(args.parent / "map_before.npz")
    final_map = load_map(args.parent / "surface_map.npz")
    chart, footprint_cells, footprint_deg = topo1a.build_chart(before_map.xyz_h, profile)
    if int(pm["footprint_cells"]) != footprint_cells or abs(float(pm["footprint_radius_deg"]) - footprint_deg) > 1e-12:
        raise AssertionError("reconstructed Cyclopean-1a chart footprint mismatch")

    evidence = _evidence(args.parent, pm, chart)
    raw, support, target_range = topo1a.rasterize_target(final_map.xyz_h, chart, footprint_cells)
    ev = boundary.EvidenceArrays(evidence.seen_target, evidence.seen_nontarget,
                                 evidence.target_range_m, evidence.nontarget_range_m)
    audit = boundary.analyze_boundary(
        raw_support=raw, support=support, target_range_m=target_range, evidence=ev,
        grid_deg=chart.grid_deg, yaw0_deg=chart.yaw0_deg, pitch0_deg=chart.pitch0_deg,
        footprint_cells=footprint_cells,
        association_radius_m=float(public.FUSION["association_radius_m"]),
    )
    report = {
        "seed": seed,
        "profile": profile,
        "chart": {"yaw0_deg": chart.yaw0_deg, "pitch0_deg": chart.pitch0_deg,
                  "grid_deg": chart.grid_deg, "width": chart.width, "height": chart.height},
        "footprint_cells": footprint_cells,
        "footprint_radius_deg": footprint_deg,
        "map_points": int(len(final_map.xyz_h)),
        "raw_support_cells": int(raw.sum()),
        "support_cells": int(support.sum()),
        "complement_cells": int((~support).sum()),
        "shoreline_cells": int(audit.shoreline.sum()),
        "components": audit.components,
        "arcs": audit.arcs,
        "summary": _summary(audit),
    }
    json_write(args.out / "boundary_report.json", report)
    _write_visual(args.out / "shoreline.png", support, audit)

    parent_hash_after = {n: _sha256(args.parent / n) for n in parent_hash_before}
    if parent_hash_after != parent_hash_before:
        raise AssertionError("Cyclopean-1a parent changed during read-only audit")
    manifest = {
        "schema": "Cyclopean1b-boundary-audit-v1",
        "public_spec_sha256": public.public_digest(),
        "parent_spec": public.PARENT_SPEC_ID,
        "parent_record": str(args.parent),
        "parent_hashes": parent_hash_before,
        "seed": seed,
        "profile": profile,
        "fixture": public.FIXTURE,
        "fixed_head": True,
        "static_scene": True,
        "truth_opened": False,
        "acquisitions_added": 0,
        "parent_files_modified": False,
        "boundary_report": "boundary_report.json",
        "visual": "shoreline.png",
        "summary": report["summary"],
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    print("[cyclopean1b-audit] COMPLETE", json.dumps({"seed": seed, **report["summary"]}, sort_keys=True), flush=True)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    execute(ap.parse_args())


if __name__ == "__main__":
    main()
