"""Run exactly one Cyclopean-1c probe into seed 2111's deepest unresolved bay."""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image

import cyclopean1a_topology as topo1a
import cyclopean1b_audit as audit1b
import cyclopean1b_boundary as boundary1b
import cyclopean1b_public as parent_public
import cyclopean1c_public as public
import cyclopean1c_bay as bay
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg3_surface_map import Patch, load_map, save_map, fuse
import fsg6_run as fsg6run
from fsg_geometry import json_write
from reality1_run import _tone_preview


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _validate_parent(parent: Path) -> dict:
    m = json.loads((parent / "prediction_manifest.json").read_text())
    if m.get("schema") != "Cyclopean1b-boundary-audit-v1":
        raise AssertionError("Cyclopean-1c requires a completed Cyclopean-1b parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("Cyclopean-1b public digest mismatch")
    if int(m.get("seed", -1)) not in public.SEEDS:
        raise AssertionError("Cyclopean-1c is scheduled only for seed 2111")
    if m.get("truth_opened") is not False or not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("Cyclopean-1b integrity contract broken")
    if int(m.get("acquisitions_added", -1)) != 0 or m.get("parent_files_modified") is not False:
        raise AssertionError("Cyclopean-1b was not a read-only parent")
    return m


def _existing_gazes(parent1a: Path) -> list[tuple[float, float]]:
    pm1a = json.loads((parent1a / "prediction_manifest.json").read_text())
    rc2b = Path(pm1a["parent_record"])
    pm2b = json.loads((rc2b / "prediction_manifest.json").read_text())
    gazes = [tuple(map(float, g)) for g in pm2b["fixation_gazes_deg"]]
    pr = pm1a.get("probe_result", {})
    if pr.get("probe_taken"):
        gazes.append(tuple(map(float, pr["probe_gaze_deg"])))
    return gazes


def _rebuild(parent1b: Path, pm1b: dict):
    parent1a = Path(pm1b["parent_record"])
    pm1a = audit1b._validate_parent(parent1a)
    chart_map = load_map(parent1a / "map_before.npz")
    sm = load_map(parent1a / "surface_map.npz")
    chart, footprint_cells, footprint_deg = topo1a.build_chart(chart_map.xyz_h, str(pm1a["profile"]))
    if int(pm1a["footprint_cells"]) != footprint_cells or abs(float(pm1a["footprint_radius_deg"]) - footprint_deg) > 1e-12:
        raise AssertionError("reconstructed inherited chart footprint mismatch")
    evidence = audit1b._evidence(parent1a, pm1a, chart)
    raw, support, target_range = topo1a.rasterize_target(sm.xyz_h, chart, footprint_cells)
    ev = boundary1b.EvidenceArrays(evidence.seen_target, evidence.seen_nontarget,
                                   evidence.target_range_m, evidence.nontarget_range_m)
    audit = boundary1b.analyze_boundary(
        raw_support=raw,
        support=support,
        target_range_m=target_range,
        evidence=ev,
        grid_deg=chart.grid_deg,
        yaw0_deg=chart.yaw0_deg,
        pitch0_deg=chart.pitch0_deg,
        footprint_cells=footprint_cells,
        association_radius_m=float(public.FUSION["association_radius_m"]),
    )
    return parent1a, pm1a, sm, chart, footprint_cells, footprint_deg, evidence, raw, support, target_range, audit


def _summary(audit) -> dict:
    ext = [c for c in audit.components if c["kind"] == "EXTERIOR"]
    internal = [c for c in audit.components if c["kind"] == "INTERNAL"]
    unobs = [a for a in audit.arcs if a["state"] == "UNOBSERVED"]
    return {
        "support_cells": int((audit.component_labels < 0).sum()),
        "complement_cells": int((audit.component_labels >= 0).sum()),
        "shoreline_cells": int(audit.shoreline.sum()),
        "exterior_components": int(len(ext)),
        "internal_components": int(len(internal)),
        "unobserved_arcs": int(len(unobs)),
        "max_exterior_border_distance_cells": max((int(c["max_border_distance_cells"]) for c in ext), default=None),
    }


def _run_blender(args, seed: int, profile: str, step: int, gaze: tuple[float, float]) -> Path:
    out = args.out / "acquisition"
    out.mkdir()
    cmd = [
        args.blender, "-b", "--python-exit-code", "1",
        "-P", "tools/reality2_render_fix.py", "--",
        "--out", str(out), "--profile", profile, "--seed", str(seed),
        "--step", str(step), "--yaw", f"{gaze[0]:.12g}",
        "--pitch", f"{gaze[1]:.12g}", "--device", args.device,
    ]
    p = subprocess.run(cmd, cwd=args.repo, text=True, capture_output=True)
    (args.out / "render.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    if p.returncode != 0:
        raise RuntimeError("Cyclopean-1c Blender probe failed; see render.log")
    return out / f"fix_{step:02d}"


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve()
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()
    pm1b = _validate_parent(args.parent)
    seed = int(pm1b["seed"])
    profile = str(pm1b["profile"])
    parent_hash_before = {n: _sha256(args.parent / n) for n in ("prediction_manifest.json", "boundary_report.json", "shoreline.png")}
    (parent1a, pm1a, sm, chart, fc, fd, evidence,
     raw_before, support_before, range_before, audit_before) = _rebuild(args.parent, pm1b)
    gazes = _existing_gazes(parent1a)
    selected = bay.select_deep_bay_probe(audit_before, chart, gazes)
    if selected is None:
        raise AssertionError("seed 2111 has no eligible exterior UNOBSERVED bay under the frozen 1b semantics")
    gaze = tuple(map(float, selected["probe_gaze_deg"]))
    if any(np.allclose(np.asarray(g, float), np.asarray(gaze, float), atol=1e-9) for g in gazes):
        raise AssertionError("bay selector returned a revisited gaze")
    audit1b._write_visual(args.out / "shoreline_before.png", support_before, audit_before)
    save_map(args.out / "map_before.npz", sm)
    step = len(gazes)
    case = _run_blender(args, seed, profile, step, gaze)
    c, obs = hdr.read_observation(case)
    rec, _, _ = compute_once(c, obs)
    m = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID)
    patch = Patch(f"cyclopean_bay_probe_{step:02d}", rec["xyz_h"][m], rec["rgb_left"][m], rec["instance_id"][m])
    np.savez_compressed(
        args.out / "probe_patch.npz",
        xyz_h=patch.xyz_h.astype(np.float32),
        rgb=patch.rgb.astype(np.float32),
        instance_id=patch.instance_id,
        valid=rec["valid"],
        oracle_instance_id=rec["instance_id"],
        raw_support_L=rec["raw_support_L"],
    )
    Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "probe_rgb.png")
    contract = __import__("reality2b_public").empty_observation_contract(len(patch.xyz_h))
    out_map = sm
    assoc = {"new": 0, "matched": 0, "input_points": int(len(patch.xyz_h))}
    idem = None
    if contract["fuse_target_points"]:
        out_map, assoc = fuse(sm, patch, public.OBJECT_ID,
                              public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"])
        replay, dup = fuse(out_map, patch, public.OBJECT_ID,
                           public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"])
        idem = bool(
            dup["duplicate_patch"]
            and np.array_equal(out_map.xyz_h, replay.xyz_h)
            and np.array_equal(out_map.support_count, replay.support_count)
            and np.array_equal(out_map.provenance_mask, replay.provenance_mask)
        )
        if not idem:
            raise AssertionError("bay probe replay is not idempotent")
    if set(np.unique(out_map.instance_id).tolist()) != {public.OBJECT_ID}:
        raise AssertionError("bay probe contaminated target map")
    topo1a.add_observation(evidence, chart, rec["xyz_h"], rec["instance_id"], rec["valid"], public.OBJECT_ID)
    raw_after, support_after, range_after = topo1a.rasterize_target(out_map.xyz_h, chart, fc)
    ev_after = boundary1b.EvidenceArrays(evidence.seen_target, evidence.seen_nontarget,
                                         evidence.target_range_m, evidence.nontarget_range_m)
    audit_after = boundary1b.analyze_boundary(
        raw_support=raw_after,
        support=support_after,
        target_range_m=range_after,
        evidence=ev_after,
        grid_deg=chart.grid_deg,
        yaw0_deg=chart.yaw0_deg,
        pitch0_deg=chart.pitch0_deg,
        footprint_cells=fc,
        association_radius_m=float(public.FUSION["association_radius_m"]),
    )
    audit1b._write_visual(args.out / "shoreline_after.png", support_after, audit_after)
    save_map(args.out / "surface_map.npz", out_map)
    fsg6run.save_ply(args.out / "surface_map.ply", out_map)
    before_summary = _summary(audit_before)
    after_summary = _summary(audit_after)
    result = {
        "probe_taken": True,
        "probe_gaze_deg": list(gaze),
        "probe_target_points": int(len(patch.xyz_h)),
        "probe_fused": bool(contract["fuse_target_points"]),
        "idempotent_replay": idem,
        "new_surfels": int(assoc.get("new", 0)),
        "matched_surfels": int(assoc.get("matched", 0)),
    }
    manifest = {
        "schema": "Cyclopean1c-bay-probe-v1",
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
        "parent_fixations_rerendered": 0,
        "added_fixations": 1,
        "grid_deg": chart.grid_deg,
        "footprint_cells": fc,
        "footprint_radius_deg": fd,
        "selected_bay": selected,
        "probe_result": result,
        "map_points_before": int(len(sm.xyz_h)),
        "map_points_after": int(len(out_map.xyz_h)),
        "boundary_before": before_summary,
        "boundary_after": after_summary,
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    parent_hash_after = {n: _sha256(args.parent / n) for n in parent_hash_before}
    if parent_hash_after != parent_hash_before:
        raise AssertionError("Cyclopean-1b parent changed during 1c")
    print("[cyclopean1c-probe] COMPLETE", json.dumps({
        "seed": seed,
        "selected_bay": selected,
        "probe": result,
        "before": before_summary,
        "after": after_summary,
    }, sort_keys=True), flush=True)
    return manifest


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--parent", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", choices=("OPTIX", "CUDA", "CPU"), default="OPTIX")
    ap.add_argument("--blender", default="blender")
    execute(ap.parse_args())


if __name__ == "__main__":
    main()
