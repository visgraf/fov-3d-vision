"""Run exactly one re-centered measurement probe on the Cyclopean-1f residue."""
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
import cyclopean1d_audit as audit1d
import cyclopean1d_epistemic as epi
import cyclopean1f_run as run1f
import cyclopean1f_public as parent_public
import cyclopean1g_measurement as measurement
import cyclopean1g_public as public
import fsg_stereo_hdr as hdr
from fsg_stereo_supported import compute_once, check_kernel_equivalence
from fsg3_surface_map import Patch, fuse, load_map, save_map
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
    if m.get("schema") != "Cyclopean1f-epistemic-loop-v1":
        raise AssertionError("Cyclopean-1g requires a completed Cyclopean-1f parent")
    if m.get("public_spec_sha256") != parent_public.public_digest():
        raise AssertionError("Cyclopean-1f public digest mismatch")
    if int(m.get("seed", -1)) != 2111 or m.get("truth_opened") is not False:
        raise AssertionError("wrong seed or truth integrity broken")
    if not m.get("fixed_head") or not m.get("static_scene"):
        raise AssertionError("fixed-head/static-scene invariant broken")
    if not m.get("scientific_stop_reached") or m.get("stop_reason") != "NO_ELIGIBLE_EXTERIOR_NEVER_OBSERVED":
        raise AssertionError("Cyclopean-1f did not reach its scientific attention fixed point")
    if int(m.get("epistemic_after", {}).get("exterior_never_observed_cells", -1)) != 0:
        raise AssertionError("Cyclopean-1f parent still has eligible NEVER_OBSERVED exterior shoreline")
    return m


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
        raise RuntimeError("Cyclopean-1g Blender probe failed; see render.log")
    return out / f"fix_{step:02d}"


def _rebuild_parent_state(parent: Path, pm1f: dict):
    """Rebuild final 1f evidence/history exactly, then use its saved final map."""
    parent1e = Path(pm1f["parent_record"])
    pm1e = run1f._validate_parent(parent1e)
    parent1c, pm1c, _sm_start, chart, fc, fd, evidence, observations, gazes = run1f._initial_state(parent1e, pm1e)

    for it in pm1f.get("iterations", []):
        step = int(it["step"])
        case = parent / "acquisitions" / f"step_{step:02d}" / f"fix_{step:02d}"
        patch_path = parent / "patches" / f"fix_{step:02d}.npz"
        if not case.is_dir() or not patch_path.is_file():
            raise AssertionError(f"missing saved Cyclopean-1f acquisition for step {step}")
        c, obs = hdr.read_observation(case)
        rec, _, _ = compute_once(c, obs)
        topo1a.add_observation(evidence, chart, rec["xyz_h"], rec["instance_id"], rec["valid"], public.OBJECT_ID)
        observations.append(audit1d._load_saved_observation(
            case / "calibration.json", patch_path, f"fix_{step:02d}"
        ))
        gazes.append(tuple(map(float, it["gaze_deg"])))

    sm = load_map(parent / "surface_map.npz")
    raw, support, audit = run1f._audit_current(sm, chart, fc, evidence)
    refined, cell_ev = audit1d._refine_unobserved(chart, audit, observations)
    summary = run1f._summary(audit, refined)
    published = pm1f.get("epistemic_after", {})
    if summary.get("exterior_never_observed_cells") != published.get("exterior_never_observed_cells"):
        raise AssertionError("Cyclopean-1g rebuild does not reproduce parent NEVER_OBSERVED count")
    if summary.get("refined_cells_by_state", {}).get("OBSERVED_TARGET_NO_DEPTH") != 28:
        raise AssertionError("expected the measured 28-cell no-depth residue in Cyclopean-1f parent")
    return parent1c, pm1c, sm, chart, fc, fd, evidence, observations, gazes, raw, support, audit, refined, cell_ev


def _component_residue_cells(audit, refined: np.ndarray, component_id: int) -> np.ndarray:
    code = epi.STATE_CODE["OBSERVED_TARGET_NO_DEPTH"]
    y, x = np.nonzero(
        audit.shoreline
        & (audit.component_labels == int(component_id))
        & (refined == code)
    )
    return np.column_stack((y, x)).astype(np.int32)


def _probe_evidence_for_cells(chart, audit, cells: np.ndarray, new_ob: dict) -> dict:
    target_seen = 0
    target_depth = 0
    nontarget_seen = 0
    unsupported = 0
    per_cell = []
    for y, x in cells:
        rho = float(audit.local_target_range_m[int(y), int(x)])
        if not np.isfinite(rho) or rho <= 0:
            per_cell.append({"y": int(y), "x": int(x), "range_reference_m": None, "supported": 0,
                             "target_seen": 0, "target_depth_valid": 0, "nontarget_seen": 0})
            unsupported += 1
            continue
        point = audit1d._cell_point(chart, int(y), int(x), rho)[None, :]
        e = epi.sample_projected_evidence(
            new_ob["calibration"], new_ob["rectification"], new_ob["instance_id"], new_ob["valid"],
            new_ob["raw_support_L"], point, public.OBJECT_ID,
        )[0]
        target_seen += int(e.target_seen)
        target_depth += int(e.target_depth_valid)
        nontarget_seen += int(e.nontarget_seen)
        unsupported += int(e.supported_projections == 0)
        per_cell.append({
            "y": int(y), "x": int(x), "range_reference_m": float(rho),
            "supported": int(e.supported_projections),
            "target_seen": int(e.target_seen),
            "target_depth_valid": int(e.target_depth_valid),
            "nontarget_seen": int(e.nontarget_seen),
        })
    return {
        "cell_count": int(len(cells)),
        "target_seen_cells": int(target_seen),
        "recovered_valid_target_cells": int(target_depth),
        "nontarget_seen_cells": int(nontarget_seen),
        "unsupported_cells": int(unsupported),
        "cells": per_cell,
    }


def execute(args) -> dict:
    args.repo = Path(args.repo).resolve()
    args.parent = Path(args.parent).resolve()
    args.out = Path(args.out).resolve()
    if args.out.exists():
        raise FileExistsError("output must be new")
    args.out.mkdir(parents=True)
    check_kernel_equivalence()

    pm1f = _validate_parent(args.parent)
    parent_hash_before = {n: _sha256(args.parent / n) for n in (
        "prediction_manifest.json", "surface_map.npz", "epistemic_final.png"
    )}
    (parent1c, pm1c, sm, chart, fc, fd, evidence, observations, gazes,
     raw_before, support_before, audit_before, refined_before, _cell_ev) = _rebuild_parent_state(args.parent, pm1f)

    selected = measurement.select_remeasurement_probe(
        shoreline=audit_before.shoreline,
        component_labels=audit_before.component_labels,
        components=audit_before.components,
        refined_state=refined_before,
        observed_target_no_depth_code=epi.STATE_CODE["OBSERVED_TARGET_NO_DEPTH"],
        chart=chart,
        existing_gazes=gazes,
    )
    if selected is None:
        raise AssertionError("no eligible INTERNAL OBSERVED_TARGET_NO_DEPTH residue exists")
    selected["refined_state"] = "OBSERVED_TARGET_NO_DEPTH"
    selected["component_kind"] = "INTERNAL"
    selected["never_observed_eligible"] = False
    gaze = tuple(map(float, selected["probe_gaze_deg"]))
    if any(np.allclose(np.asarray(g, float), np.asarray(gaze, float), atol=1e-9) for g in gazes):
        raise AssertionError("re-centered measurement selector returned a revisited gaze")

    selected_cells = _component_residue_cells(audit_before, refined_before, int(selected["component_id"]))
    if len(selected_cells) != int(selected["observed_target_no_depth_cells"]):
        raise AssertionError("selected residue cell count changed during selection")
    rho_values = np.array([
        float(audit_before.local_target_range_m[int(y), int(x)]) for y, x in selected_cells
    ], float)
    if not np.all(np.isfinite(rho_values)):
        raise AssertionError("OBSERVED_TARGET_NO_DEPTH residue unexpectedly lacks range references")
    selected["local_range_reference_median"] = float(np.median(rho_values))
    selected["local_range_reference_min"] = float(np.min(rho_values))
    selected["local_range_reference_max"] = float(np.max(rho_values))

    audit1d._write_visual(args.out / "epistemic_before.png", support_before, audit_before, refined_before)
    save_map(args.out / "map_before.npz", sm)

    seed = int(pm1f["seed"]); profile = str(pm1f["profile"]); step = len(gazes)
    case = _run_blender(args, seed, profile, step, gaze)
    c, obs = hdr.read_observation(case)
    rec, _, _ = compute_once(c, obs)
    target = rec["valid"] & (rec["instance_id"] == public.OBJECT_ID)
    patch = Patch(
        f"cyclopean1g_recentered_fix_{step:02d}",
        rec["xyz_h"][target], rec["rgb_left"][target], rec["instance_id"][target],
    )
    patch_path = args.out / "probe_patch.npz"
    np.savez_compressed(
        patch_path,
        xyz_h=patch.xyz_h.astype(np.float32), rgb=patch.rgb.astype(np.float32), instance_id=patch.instance_id,
        valid=rec["valid"], oracle_instance_id=rec["instance_id"], raw_support_L=rec["raw_support_L"],
    )
    Image.fromarray(_tone_preview(rec["rgb_left"])).save(args.out / "probe_rgb.png")
    new_ob = audit1d._load_saved_observation(case / "calibration.json", patch_path, f"fix_{step:02d}")
    recovery = _probe_evidence_for_cells(chart, audit_before, selected_cells, new_ob)
    outcome = measurement.classify_measurement_outcome(
        recovered_valid_target_cells=recovery["recovered_valid_target_cells"]
    )

    contract = __import__("reality2b_public").empty_observation_contract(len(patch.xyz_h))
    out_map = sm
    assoc = {"new": 0, "matched": 0, "input_points": int(len(patch.xyz_h))}
    idem = None
    if contract["fuse_target_points"]:
        out_map, assoc = fuse(
            sm, patch, public.OBJECT_ID,
            public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
        )
        replay, dup = fuse(
            out_map, patch, public.OBJECT_ID,
            public.FUSION["association_radius_m"], public.FUSION["hash_cell_m"],
        )
        idem = bool(
            dup["duplicate_patch"]
            and np.array_equal(out_map.xyz_h, replay.xyz_h)
            and np.array_equal(out_map.support_count, replay.support_count)
            and np.array_equal(out_map.provenance_mask, replay.provenance_mask)
        )
        if not idem:
            raise AssertionError("Cyclopean-1g probe replay is not idempotent")
    if set(np.unique(out_map.instance_id).tolist()) != {public.OBJECT_ID}:
        raise AssertionError("Cyclopean-1g contaminated target map")

    topo1a.add_observation(evidence, chart, rec["xyz_h"], rec["instance_id"], rec["valid"], public.OBJECT_ID)
    observations_after = observations + [new_ob]
    raw_after, support_after, audit_after = run1f._audit_current(out_map, chart, fc, evidence)
    refined_after, _ev_after = audit1d._refine_unobserved(chart, audit_after, observations_after)
    audit1d._write_visual(args.out / "epistemic_after.png", support_after, audit_after, refined_after)
    save_map(args.out / "surface_map.npz", out_map)
    fsg6run.save_ply(args.out / "surface_map.ply", out_map)

    no_depth_before = int((refined_before == epi.STATE_CODE["OBSERVED_TARGET_NO_DEPTH"]).sum())
    no_depth_after = int((refined_after == epi.STATE_CODE["OBSERVED_TARGET_NO_DEPTH"]).sum())
    manifest = {
        "schema": "Cyclopean1g-recentered-measurement-v1",
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
        "total_fixations_before": int(len(gazes)),
        "total_fixations_after": int(len(gazes) + 1),
        "measurement_change": "recenter OBSERVED_TARGET_NO_DEPTH residue; frozen stereo/vergence/render settings",
        "selected": selected,
        "probe_result": {
            "probe_gaze_deg": [float(gaze[0]), float(gaze[1])],
            "probe_target_points": int(len(patch.xyz_h)),
            "new_surfels": int(assoc.get("new", 0)),
            "matched_surfels": int(assoc.get("matched", 0)),
            "idempotent_replay": idem,
            "selected_residue_cells": int(len(selected_cells)),
            "selected_residue_recovery": recovery,
            "measurement_outcome": outcome,
        },
        "map_points_before": int(len(sm.xyz_h)),
        "map_points_after": int(len(out_map.xyz_h)),
        "observed_target_no_depth_before": no_depth_before,
        "observed_target_no_depth_after": no_depth_after,
        "branch_disposition": "STOP_AFTER_ONE_LOOK_REGARDLESS_OF_OUTCOME_THEN_MOVE_TO_MULTI_OBJECT",
    }
    json_write(args.out / "prediction_manifest.json", manifest)

    parent_hash_after = {n: _sha256(args.parent / n) for n in parent_hash_before}
    if parent_hash_after != parent_hash_before:
        raise AssertionError("Cyclopean-1f parent changed during 1g")

    print("[cyclopean1g-probe] COMPLETE", json.dumps({
        "seed": seed,
        "gaze_deg": manifest["probe_result"]["probe_gaze_deg"],
        "selected_residue_cells": len(selected_cells),
        "recovered_valid_target_cells": recovery["recovered_valid_target_cells"],
        "measurement_outcome": outcome,
        "new_surfels": int(assoc.get("new", 0)),
        "no_depth_before": no_depth_before,
        "no_depth_after": no_depth_after,
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
