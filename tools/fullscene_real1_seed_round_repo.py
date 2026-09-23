"""Live-repository seam for the one-round visible-seed recovery experiment.

Claude Code may complete this NEW file against the live repository. Existing
renderer, stereo, seed, fusion, FSG, audit, REAL-1 baseline, and evaluator
sources remain frozen.

Everything below composes already-established mechanisms unchanged: the generic
procedural acquisition renderer (tools/scene_render_fix.py), the current stereo
front end (fsg_stereo_supported.compute_once), and the FullScene-1b
selected-object seed extraction/purity semantics. No evaluator-side module is
imported here, and no reference panorama is read during probe selection.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Any

import numpy as np
from PIL import Image

import fsg_stereo_hdr as hdr
from fsg_stereo_supported import check_kernel_equivalence, compute_once
from reality1_run import _tone_preview

# The baseline REAL-1 record was acquired on the "full" profile; probes must be
# taken through the same unchanged instrument to be comparable to it.
PROFILE = "full"
RENDERER = "tools/scene_render_fix.py"

# Baseline artifacts pinned for the read-only proof. Per-object map files are
# added dynamically from the baseline's own status table.
BASELINE_PINNED = (
    "scene_manifest.json",
    "observer_complete.json",
    "object_status_table.json",
    "fixation_history.json",
    "enumeration_oracle.json",
    "scene_points.npz",
    "observer_depth.npy",
    "observer_instance.npy",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


class SeedRoundRepository:
    def __init__(self, repo: Path, baseline_out: Path, out: Path, seed: int):
        self.repo = Path(repo).resolve()
        self.baseline_out = Path(baseline_out).resolve()
        self.out = Path(out).resolve()
        self.seed = int(seed)
        self.blender = "blender"
        self.device = "OPTIX"
        self.blender_launches = 0
        self.render_seconds = 0.0
        self._baseline_hashes: dict[str, str] = {}
        self._kernel_checked = False

    # ---------- baseline (strictly read-only) ----------

    def load_baseline(self) -> dict[str, Any]:
        """Return sealed REAL-1 manifest/status/fixation data; never mutate baseline files."""
        manifest_path = self.baseline_out / "scene_manifest.json"
        seal_path = self.baseline_out / "observer_complete.json"
        status_path = self.baseline_out / "object_status_table.json"
        history_path = self.baseline_out / "fixation_history.json"
        for p in (manifest_path, seal_path, status_path, history_path):
            if not p.is_file():
                raise FileNotFoundError(f"baseline REAL-1 artifact missing: {p}")

        manifest = json.loads(manifest_path.read_text())
        seal = json.loads(seal_path.read_text())
        rows = json.loads(status_path.read_text())
        history = json.loads(history_path.read_text())

        if seal.get("observer_sealed") is not True:
            raise AssertionError("baseline REAL-1 observer is not sealed")
        if manifest.get("observer_sealed_before_truth") is not True:
            raise AssertionError("baseline REAL-1 did not seal before opening truth")
        if manifest.get("structural_fails") != []:
            raise AssertionError("baseline REAL-1 record is structurally incomplete")
        if int(manifest.get("seed", -1)) != self.seed:
            raise AssertionError("baseline REAL-1 seed does not match this round")

        # The baseline records each object's oracle direction as one
        # oracle_seed_gaze_deg pair; the round driver reads it as two scalars.
        # Project it without altering the baseline file.
        normalized: list[dict[str, Any]] = []
        for row in rows:
            r = dict(row)
            gaze = r.get("oracle_seed_gaze_deg")
            if gaze is None or len(gaze) != 2:
                raise AssertionError(f"baseline row {r.get('object_id')} has no oracle seed direction")
            r["seed_yaw_deg"] = float(gaze[0])
            r["seed_pitch_deg"] = float(gaze[1])
            normalized.append(r)

        # Pin everything that must stay byte-identical, including every
        # per-object map the baseline produced.
        pinned = list(BASELINE_PINNED)
        for r in normalized:
            for key in ("map_npz", "map_ply"):
                rel = r.get(key)
                if rel:
                    pinned.append(str(rel))
        self._baseline_hashes = {
            name: _sha256(self.baseline_out / name)
            for name in pinned
            if (self.baseline_out / name).is_file()
        }

        return {
            "object_rows": normalized,
            "fixation_steps": [int(f["global_step"]) for f in history],
            "manifest": manifest,
            "baseline_seal_sha256": _sha256(seal_path),
            "baseline_hashes": dict(self._baseline_hashes),
        }

    def verify_baseline_unchanged(self) -> dict[str, Any]:
        """Re-hash every pinned baseline artifact and refuse any difference."""
        if not self._baseline_hashes:
            raise AssertionError("baseline was never pinned")
        after = {name: _sha256(self.baseline_out / name) for name in self._baseline_hashes}
        changed = [n for n in after if after[n] != self._baseline_hashes[n]]
        if changed:
            raise AssertionError(f"baseline REAL-1 artifacts changed during the round: {changed}")
        return {
            "baseline_files_pinned": len(after),
            "baseline_files_changed": 0,
            "baseline_hashes_after": after,
        }

    # ---------- acquisition (observer-side only) ----------

    def _render(self, step: int, gaze: tuple[float, float], probe_dir: Path) -> Path:
        """One physical fixation through the unchanged generic scene renderer."""
        out = probe_dir / "acquisition"
        logs = probe_dir / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        yaw, pitch = float(gaze[0]), float(gaze[1])
        cmd = [
            self.blender, "-b", "--python-exit-code", "1", "-P", RENDERER, "--",
            "--out", str(out), "--profile", PROFILE, "--seed", str(self.seed),
            "--step", str(step), "--yaw", f"{yaw:.12g}", "--pitch", f"{pitch:.12g}",
            "--device", self.device,
        ]
        t0 = time.perf_counter()
        p = subprocess.run(cmd, cwd=self.repo, text=True, capture_output=True)
        self.blender_launches += 1
        self.render_seconds += time.perf_counter() - t0
        (logs / f"render_{step:02d}.log").write_text(p.stdout + "\n--- STDERR ---\n" + p.stderr)
        if p.returncode != 0:
            raise RuntimeError(f"seed-round Blender probe {step} failed; see {logs}")
        rr = json.loads((out / "run.json").read_text())
        if not rr.get("complete") or int(rr.get("seed", -1)) != self.seed or int(rr.get("step", -1)) != step:
            raise RuntimeError("incomplete or wrong seed-round acquisition record")
        if abs(float(rr["yaw_deg"]) - yaw) > 1e-8 or abs(float(rr["pitch_deg"]) - pitch) > 1e-8:
            raise RuntimeError("Blender record gaze mismatch")
        return out / f"fix_{step:02d}"

    def acquire_probe(self, target_row: dict[str, Any], gaze_deg: tuple[float, float],
                      global_step: int, probe_dir: Path) -> dict[str, Any]:
        """Render exactly one generic fixation and run the unchanged stereo front end.

        Return observer-side target visible-pixel and valid-depth counts plus
        enough saved evidence to materialize a selected-object seed from this
        SAME observation. Evaluator truth/reference data must not be read here.
        """
        if not self._kernel_checked:
            check_kernel_equivalence()
            self._kernel_checked = True
        oid = int(target_row["object_id"])
        case = self._render(int(global_step), gaze_deg, probe_dir)
        c, obs = hdr.read_observation(case)
        rec, _meta, _state = compute_once(c, obs)

        ids = np.asarray(rec["instance_id"])
        valid = np.asarray(rec["valid"], bool)
        visible = int(np.count_nonzero(ids == oid))
        valid_depth = int(np.count_nonzero(valid & (ids == oid)))
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(probe_dir / "probe_rgb.png")

        # Descriptive only; never used to rank or gate.
        other_ids, other_counts = np.unique(ids[ids > 0], return_counts=True)
        return {
            "object_id": oid,
            "target_visible_pixels": visible,
            "target_valid_depth_count": valid_depth,
            "target_depth_recovery_fraction": (float(valid_depth / visible) if visible else None),
            "frame_pixels": int(valid.size),
            "frame_valid_pixels": int(valid.sum()),
            "frame_valid_fraction": float(valid.mean()),
            "frame_instance_histogram": {str(int(i)): int(n) for i, n in zip(other_ids, other_counts)},
            "case": str(case),
            "evaluator_truth_consulted": False,
        }

    # ---------- established seed materialization, same observation ----------

    def materialize_seed_from_probe(self, target_row: dict[str, Any], probe: dict[str, Any],
                                    object_dir: Path) -> dict[str, Any]:
        """Apply established selected-object seed extraction/purity semantics to the winning probe."""
        oid = int(target_row["object_id"])
        case = Path(probe["case"])
        if not (case / "calibration.json").is_file() or not (case / "observation.npz").is_file():
            raise FileNotFoundError(f"winning probe acquisition missing: {case}")

        # Re-read the SAME saved acquisition. No ninth fixation is rendered.
        c, obs = hdr.read_observation(case)
        rec, _meta, _state = compute_once(c, obs)

        # Verbatim FullScene-1b selected-object seed extraction.
        valid = np.asarray(rec["valid"], dtype=bool)
        instance_id = np.asarray(rec["instance_id"])
        target = valid & (instance_id == oid)
        xyz = np.asarray(rec["xyz_h"][target], dtype=np.float32)
        rgb = np.asarray(rec["rgb_left"][target], dtype=np.float32)
        ids = np.asarray(instance_id[target])

        if int(len(xyz)) != int(probe["target_valid_depth_count"]):
            raise AssertionError("re-read winning probe disagrees with its recorded target count")
        pure = bool(len(ids) == 0 or set(np.unique(ids).tolist()) == {oid})
        if not pure:
            raise AssertionError("recovered seed patch is not pure for the target object")

        patch_name = f"object_{oid}_seed_patch.npz"
        np.savez_compressed(
            object_dir / patch_name,
            xyz_h=xyz,
            rgb=rgb,
            instance_id=ids,
            valid=valid,
            oracle_instance_id=instance_id,
            raw_support_L=np.asarray(rec["raw_support_L"], bool),
        )
        Image.fromarray(_tone_preview(rec["rgb_left"])).save(object_dir / f"object_{oid}_seed_rgb.png")
        np.save(object_dir / f"object_{oid}_seed_xyz.npy", xyz)

        rng = np.linalg.norm(xyz.astype(np.float64), axis=1) if len(xyz) else np.empty(0)
        return {
            "object_id": oid,
            "seed_patch": patch_name,
            "seed_rgb": f"object_{oid}_seed_rgb.png",
            "rendered_new_fixation": False,
            "reused_probe_ring_order": int(probe["ring_order"]),
            "reused_probe_global_step": int(probe["global_step"]),
            "gaze_deg": list(probe["gaze_deg"]),
            "seed_points": int(len(xyz)),
            "seed_patch_pure": pure,
            "target_visible_pixels": int(probe["target_visible_pixels"]),
            "target_depth_recovery_fraction": probe.get("target_depth_recovery_fraction"),
            "range_min_m": (float(rng.min()) if len(rng) else None),
            "range_median_m": (float(np.median(rng)) if len(rng) else None),
            "range_max_m": (float(rng.max()) if len(rng) else None),
            # Reported, never applied as a gate here: the frozen FSG3
            # initialize() refuses fewer than 100 points, which is also the
            # inherited empty-look limit. This round introduces no threshold of
            # its own and does not initialize a map.
            "frozen_map_initialize_minimum_points": 100,
            "would_satisfy_frozen_map_initialize": bool(len(xyz) >= 100),
            "map_initialized": False,
            "growth_started": False,
        }
