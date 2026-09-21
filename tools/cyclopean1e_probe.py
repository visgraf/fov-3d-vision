"""Run exactly one Cyclopean-1e fixation selected from refined NEVER_OBSERVED shoreline."""
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
import cyclopean1c_probe as probe1c
import cyclopean1d_audit as audit1d
import cyclopean1d_epistemic as epi
import cyclopean1d_public as parent_public
import cyclopean1e_public as public
import cyclopean1e_gaze as gaze_selector
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg3_surface_map import Patch, save_map, fuse
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
    if m.get("schema") != "Cyclopean1d-observation-measurement-audit-v1":
        raise AssertionError("Cyclopean-1e requires a completed Cyclopean-1d parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("Cyclopean-1d public digest mismatch")
    if int(m.get("seed", -1)) != 2111 or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("fixed-head/static-scene invariant broken")
    if int(m.get("acquisitions_added", -1)) != 0 or m.get("parent_files_modified") is not False:
        raise AssertionError("Cyclopean-1d was not a read-only parent")
    return m


def _existing_gazes(parent1c: Path, pm1c: dict, parent1a: Path) -> list[tuple[float, float]]:
    gazes = probe1c._existing_gazes(parent1a)
    pr = pm1c.get("probe_result", {})
    if not pr.get("probe_taken"):
        raise AssertionError("Cyclopean-1c parent did not take its one probe")
    gazes.append(tuple(map(float, pr["probe_gaze_deg"])))
    return gazes


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
        raise RuntimeError("Cyclopean-1e Blender probe failed; see render.log")
    return out / f"fix_{step:02d}"


def _summary(audit, refined: np.ndarray) -> dict:
    ext = [c for c in audit.components if c["kind"] == "EXTERIOR"]
    internal = [c for c in audit.components if c["kind"] == "INTERNAL"]
    counts = {name: int((refined == code).sum()) for name, code in epi.STATE_CODE.items()}
    never = epi.STATE_CODE["NEVER_OBSERVED"]
    emask = audit.shoreline & (refined == never) & (audit.exterior_distance_cells >= 0)
    return {
        "support_cells": int((audit.component_labels < 0).sum()),
        "complement_cells": int((audit.component_labels >= 0).sum()),
        "shoreline_cells": int(audit.shoreline.sum()),
        "exterior_components": int(len(ext)),
        "internal_components": int(len(internal)),
        "refined_cells_by_state": counts,
        "exterior_never_observed_cells": int(emask.sum()),
        "max_exterior_never_observed_depth_cells": int(np.max(audit.exterior_distance_cells[emask])) if np.any(emask) else None,
    }


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve()
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()

    pm1d = _validate_parent(args.parent)
    parent1c = Path(pm1d["parent_record"])
    pm1c = audit1d._validate_parent(parent1c)
    seed = int(pm1d["seed"])
    profile = str(pm1d["profile"])
    parent_hash_before = {n: _sha256(args.parent / n) for n in (
        "prediction_manifest.json", "observation_measurement_report.json", "epistemic_shoreline.png")}

    parent1a, pm1a, sm, chart, fc, fd, raw_before, support_before, audit_before = audit1d._rebuild_final_boundary(parent1c, pm1c)
    observations, _ancestry = audit1d._observation_history(parent1c, pm1c)
    refined_before, _cell_ev = audit1d._refine_unobserved(chart, audit_before, observations)
    gazes = _existing_gazes(parent1c, pm1c, parent1a)

    selected = gaze_selector.select_epistemic_probe(
        shoreline=audit_before.shoreline,
        component_labels=audit_before.component_labels,
        components=audit_before.components,
        exterior_distance_cells=audit_before.exterior_distance_cells,
        refined_state=refined_before,
        never_observed_code=epi.STATE_CODE["NEVER_OBSERVED"],
        chart=chart,
        existing_gazes=gazes,
    )
    if selected is None:
        raise AssertionError("no eligible EXTERIOR NEVER_OBSERVED shoreline remains")
    selected["refined_state"] = "NEVER_OBSERVED"
    selected["component_kind"] = "EXTERIOR"
    selected["observed_target_no_depth_eligible"] = False
    gaze = tuple(map(float, selected["probe_gaze_deg"]))
    if any(np.allclose(np.asarray(g, float), np.asarray(gaze, float), atol=1e-9) for g in gazes):
        raise AssertionError("epistemic selector returned a revisited gaze")

    audit1d._write_visual(args.out / "epistemic_before.png", support_before, audit_before, refined_before)
    save_map(args.out / "map_before.npz", sm)
    before_summary = _summary(audit_before, refined_before)

    step = len(gazes)
    case = _run_blender(args, seed, profile, step, gaze)
    c, obs = hdr.read_observation(case)
    rec, _, _ = compute_once(c, obs)
    target = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID)
    patch = Patch(
        f"cyclopean_epistemic_probe_{step:02d}",
        rec["xyz_h"][target], rec["rgb_left"][target], rec["instance_id"][target],
    )
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
            raise AssertionError("epistemic probe replay is not idempotent")
    if set(np.unique(out_map.instance_id).tolist()) != {public.OBJECT_ID}:
        raise AssertionError("epistemic probe contaminated target map")

    # Update the inherited observation evidence and rebuild both geometric and
    # epistemic shoreline state after exactly this one new look.
    # audit1d._rebuild_final_boundary already incorporated fix_13 into evidence;
    # recreate that evidence lineage from the Cyclopean-1b parent, then add fix_13
    # and this new fixation explicitly so the post-probe boundary has all looks.
    parent1b = Path(pm1c["parent_record"])
    pm1b = probe1c._validate_parent(parent1b)
    (p1a, _pm1a2, _sm1a, chart2, _fc2, _fd2, evidence,
     _rb, _sb, _rr, _ab) = probe1c._rebuild(parent1b, pm1b)
    dirs1c = sorted((parent1c / "acquisition").glob("fix_*"))
    c13, o13 = hdr.read_observation(dirs1c[0])
    r13, _, _ = compute_once(c13, o13)
    topo1a.add_observation(evidence, chart2, r13["xyz_h"], r13["instance_id"], r13["valid"], public.OBJECT_ID)
    topo1a.add_observation(evidence, chart2, rec["xyz_h"], rec["instance_id"], rec["valid"], public.OBJECT_ID)

    raw_after, support_after, range_after = topo1a.rasterize_target(out_map.xyz_h, chart, fc)
    ev_after = boundary1b.EvidenceArrays(
        evidence.seen_target, evidence.seen_nontarget,
        evidence.target_range_m, evidence.nontarget_range_m,
    )
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
    new_ob = audit1d._load_saved_observation(
        case / "calibration.json", args.out / "probe_patch.npz", f"fix_{step:02d}"
    )
    refined_after, _after_ev = audit1d._refine_unobserved(
        chart, audit_after, observations + [new_ob]
    )
    audit1d._write_visual(args.out / "epistemic_after.png", support_after, audit_after, refined_after)
    save_map(args.out / "surface_map.npz", out_map)
    fsg6run.save_ply(args.out / "surface_map.ply", out_map)
    after_summary = _summary(audit_after, refined_after)

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
        "schema": "Cyclopean1e-epistemic-gaze-v1",
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
        "selected_epistemic_region": selected,
        "probe_result": result,
        "map_points_before": int(len(sm.xyz_h)),
        "map_points_after": int(len(out_map.xyz_h)),
        "epistemic_before": before_summary,
        "epistemic_after": after_summary,
    }
    json_write(args.out / "prediction_manifest.json", manifest)

    parent_hash_after = {n: _sha256(args.parent / n) for n in parent_hash_before}
    if parent_hash_after != parent_hash_before:
        raise AssertionError("Cyclopean-1d parent changed during 1e")
    print("[cyclopean1e-probe] COMPLETE", json.dumps({
        "seed": seed,
        "selected": selected,
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
