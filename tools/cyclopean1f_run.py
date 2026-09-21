"""Iterate the frozen Cyclopean-1e epistemic gaze rule to its eligible-state fixed point."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

import cyclopean1a_topology as topo1a
import cyclopean1b_boundary as boundary1b
import cyclopean1c_probe as probe1c
import cyclopean1d_audit as audit1d
import cyclopean1d_epistemic as epi
import cyclopean1e_gaze as gaze_selector
import cyclopean1e_probe as probe1e
import cyclopean1e_public as parent_public
import cyclopean1f_loop as loop_semantics
import cyclopean1f_public as public
import fsg6_run as fsg6run
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg3_surface_map import Patch, fuse, load_map, save_map
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
    if m.get("schema") != "Cyclopean1e-epistemic-gaze-v1":
        raise AssertionError("Cyclopean-1f requires a completed Cyclopean-1e parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("Cyclopean-1e public digest mismatch")
    if int(m.get("seed", -1)) != 2111 or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("fixed-head/static-scene invariant broken")
    if int(m.get("added_fixations", -1)) != 1 or int(m.get("parent_fixations_rerendered", -1)) != 0:
        raise AssertionError("Cyclopean-1e acquisition contract mismatch")
    return m


def _summary(audit, refined: np.ndarray) -> dict:
    return probe1e._summary(audit, refined)


def _run_blender(args, seed: int, profile: str, step: int, gaze: tuple[float, float]) -> Path:
    root = args.out / "acquisitions" / f"step_{step:02d}"
    root.mkdir(parents=True)
    cmd = [
        args.blender, "-b", "--python-exit-code", "1",
        "-P", "tools/reality2_render_fix.py", "--",
        "--out", str(root), "--profile", profile, "--seed", str(seed),
        "--step", str(step), "--yaw", f"{gaze[0]:.12g}",
        "--pitch", f"{gaze[1]:.12g}", "--device", args.device,
    ]
    p = subprocess.run(cmd, cwd=args.repo, text=True, capture_output=True)
    (args.out / f"render_fix_{step:02d}.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
    if p.returncode != 0:
        raise RuntimeError(f"Cyclopean-1f Blender fixation {step} failed; see render log")
    return root / f"fix_{step:02d}"


def _initial_state(parent: Path, pm1e: dict):
    parent1d = Path(pm1e["parent_record"])
    pm1d = json.loads((parent1d / "prediction_manifest.json").read_text())
    if pm1d.get("schema") != "Cyclopean1d-observation-measurement-audit-v1":
        raise AssertionError("Cyclopean-1e ancestry does not point to Cyclopean-1d")
    parent1c = Path(pm1d["parent_record"])
    pm1c = audit1d._validate_parent(parent1c)
    parent1b = Path(pm1c["parent_record"])
    pm1b = probe1c._validate_parent(parent1b)
    parent1a, _pm1a, _sm1a, chart, fc, fd, evidence, _rb, _sb, _rr, _ab = probe1c._rebuild(parent1b, pm1b)

    dirs1c = sorted((parent1c / "acquisition").glob("fix_*"))
    if len(dirs1c) != 1:
        raise AssertionError("Cyclopean-1c probe acquisition not unique")
    c13, o13 = hdr.read_observation(dirs1c[0])
    r13, _, _ = compute_once(c13, o13)
    topo1a.add_observation(evidence, chart, r13["xyz_h"], r13["instance_id"], r13["valid"], public.OBJECT_ID)

    dirs1e = sorted((parent / "acquisition").glob("fix_*"))
    if len(dirs1e) != 1:
        raise AssertionError("Cyclopean-1e probe acquisition not unique")
    c14, o14 = hdr.read_observation(dirs1e[0])
    r14, _, _ = compute_once(c14, o14)
    topo1a.add_observation(evidence, chart, r14["xyz_h"], r14["instance_id"], r14["valid"], public.OBJECT_ID)

    observations, _ancestry = audit1d._observation_history(parent1c, pm1c)
    observations.append(audit1d._load_saved_observation(
        dirs1e[0] / "calibration.json", parent / "probe_patch.npz", dirs1e[0].name
    ))

    gazes = probe1e._existing_gazes(parent1c, pm1c, parent1a)
    gazes.append(tuple(map(float, pm1e["probe_result"]["probe_gaze_deg"])))
    sm = load_map(parent / "surface_map.npz")
    return parent1c, pm1c, sm, chart, fc, fd, evidence, observations, gazes


def _audit_current(sm, chart, fc: int, evidence):
    raw, support, target_range = topo1a.rasterize_target(sm.xyz_h, chart, fc)
    ev = boundary1b.EvidenceArrays(
        evidence.seen_target, evidence.seen_nontarget,
        evidence.target_range_m, evidence.nontarget_range_m,
    )
    audit = boundary1b.analyze_boundary(
        raw_support=raw,
        support=support,
        target_range_m=target_range,
        evidence=ev,
        grid_deg=chart.grid_deg,
        yaw0_deg=chart.yaw0_deg,
        pitch0_deg=chart.pitch0_deg,
        footprint_cells=fc,
        association_radius_m=float(public.FUSION["association_radius_m"]),
    )
    return raw, support, audit


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve()
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    (args.out / "patches").mkdir()

    check_kernel_equivalence()
    pm1e = _validate_parent(args.parent)
    parent_hash_before = {n: _sha256(args.parent / n) for n in (
        "prediction_manifest.json", "surface_map.npz", "probe_patch.npz", "epistemic_after.png"
    )}
    parent1c, pm1c, sm, chart, fc, fd, evidence, observations, gazes = _initial_state(args.parent, pm1e)
    seed = int(pm1e["seed"])
    profile = str(pm1e["profile"])

    raw, support, audit = _audit_current(sm, chart, fc, evidence)
    refined, _ = audit1d._refine_unobserved(chart, audit, observations)
    before_summary = _summary(audit, refined)
    published = pm1e.get("epistemic_after", {})
    for key in ("exterior_never_observed_cells", "max_exterior_never_observed_depth_cells"):
        if before_summary.get(key) != published.get(key):
            raise AssertionError(f"Cyclopean-1f rebuild does not reproduce parent field {key}")

    save_map(args.out / "map_before.npz", sm)
    audit1d._write_visual(args.out / "epistemic_initial.png", support, audit, refined)
    initial_map_points = int(len(sm.xyz_h))
    trace = []
    stop_reason = None

    while True:
        selected = gaze_selector.select_epistemic_probe(
            shoreline=audit.shoreline,
            component_labels=audit.component_labels,
            components=audit.components,
            exterior_distance_cells=audit.exterior_distance_cells,
            refined_state=refined,
            never_observed_code=epi.STATE_CODE["NEVER_OBSERVED"],
            chart=chart,
            existing_gazes=gazes,
        )
        decision = loop_semantics.decide(
            eligible_probe_exists=selected is not None,
            total_fixations=len(gazes),
            watchdog_total_fixations=public.WATCHDOG_TOTAL_FIXATIONS,
        )
        if decision.action == "STOP":
            stop_reason = decision.reason
            break

        selected["refined_state"] = "NEVER_OBSERVED"
        selected["component_kind"] = "EXTERIOR"
        selected["observed_target_no_depth_eligible"] = False
        gaze = tuple(map(float, selected["probe_gaze_deg"]))
        if any(np.allclose(np.asarray(g, float), np.asarray(gaze, float), atol=1e-9) for g in gazes):
            raise AssertionError("epistemic selector returned a revisited gaze")

        step = len(gazes)
        state_before = _summary(audit, refined)
        case = _run_blender(args, seed, profile, step, gaze)
        c, obs = hdr.read_observation(case)
        rec, _, _ = compute_once(c, obs)
        target = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID)
        patch = Patch(
            f"cyclopean1f_epistemic_fix_{step:02d}",
            rec["xyz_h"][target], rec["rgb_left"][target], rec["instance_id"][target],
        )
        patch_path = args.out / "patches" / f"fix_{step:02d}.npz"
        np.savez_compressed(
            patch_path,
            xyz_h=patch.xyz_h.astype(np.float32),
            rgb=patch.rgb.astype(np.float32),
            instance_id=patch.instance_id,
            valid=rec["valid"],
            oracle_instance_id=rec["instance_id"],
            raw_support_L=rec["raw_support_L"],
        )
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / f"probe_rgb_fix_{step:02d}.png")

        contract = __import__("reality2b_public").empty_observation_contract(len(patch.xyz_h))
        assoc = {"new": 0, "matched": 0, "input_points": int(len(patch.xyz_h))}
        idem = None
        if contract["fuse_target_points"]:
            new_map, assoc = fuse(
                sm, patch, public.OBJECT_ID,
                public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
            )
            replay, dup = fuse(
                new_map, patch, public.OBJECT_ID,
                public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
            )
            idem = bool(
                dup["duplicate_patch"]
                and np.array_equal(new_map.xyz_h, replay.xyz_h)
                and np.array_equal(new_map.support_count, replay.support_count)
                and np.array_equal(new_map.provenance_mask, replay.provenance_mask)
            )
            if not idem:
                raise AssertionError("Cyclopean-1f probe replay is not idempotent")
            sm = new_map
        if set(np.unique(sm.instance_id).tolist()) != {public.OBJECT_ID}:
            raise AssertionError("Cyclopean-1f contaminated target map")

        topo1a.add_observation(evidence, chart, rec["xyz_h"], rec["instance_id"], rec["valid"], public.OBJECT_ID)
        new_ob = audit1d._load_saved_observation(case / "calibration.json", patch_path, f"fix_{step:02d}")
        observations.append(new_ob)
        gazes.append(gaze)
        raw, support, audit = _audit_current(sm, chart, fc, evidence)
        refined, _ = audit1d._refine_unobserved(chart, audit, observations)
        state_after = _summary(audit, refined)
        trace.append({
            "step": int(step),
            "selected": selected,
            "gaze_deg": [float(gaze[0]), float(gaze[1])],
            "target_points": int(len(patch.xyz_h)),
            "fused": bool(contract["fuse_target_points"]),
            "new_surfels": int(assoc.get("new", 0)),
            "matched_surfels": int(assoc.get("matched", 0)),
            "idempotent_replay": idem,
            "epistemic_before": state_before,
            "epistemic_after": state_after,
        })
        print("[cyclopean1f-step]", json.dumps(trace[-1], sort_keys=True), flush=True)

    final_summary = _summary(audit, refined)
    audit1d._write_visual(args.out / "epistemic_final.png", support, audit, refined)
    save_map(args.out / "surface_map.npz", sm)
    fsg6run.save_ply(args.out / "surface_map.ply", sm)

    scientific_stop = stop_reason == "NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED"
    manifest = {
        "schema": "Cyclopean1f-epistemic-loop-v1",
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
        "added_fixations": int(len(trace)),
        "total_fixations_before": int(len(gazes) - len(trace)),
        "total_fixations_after": int(len(gazes)),
        "watchdog_total_fixations": int(public.WATCHDOG_TOTAL_FIXATIONS),
        "scientific_stop_reached": bool(scientific_stop),
        "stop_reason": stop_reason,
        "grid_deg": chart.grid_deg,
        "footprint_cells": fc,
        "footprint_radius_deg": fd,
        "map_points_before": initial_map_points,
        "map_points_after": int(len(sm.xyz_h)),
        "epistemic_before": before_summary,
        "epistemic_after": final_summary,
        "iterations": trace,
    }
    json_write(args.out / "prediction_manifest.json", manifest)
    parent_hash_after = {n: _sha256(args.parent / n) for n in parent_hash_before}
    if parent_hash_after != parent_hash_before:
        raise AssertionError("Cyclopean-1e parent changed during 1f")

    print("[cyclopean1f-run] COMPLETE", json.dumps({
        "seed": seed,
        "added_fixations": len(trace),
        "stop_reason": stop_reason,
        "scientific_stop_reached": scientific_stop,
        "before": before_summary,
        "after": final_summary,
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
