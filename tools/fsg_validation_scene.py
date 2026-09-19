"""FSG1d fixed prospective validation specification; NumPy + standard library only.

No stereo or evaluator is imported here, so Blender can use this module.
Textures and geometry are changed, not the instrument or lighting. The two
Monte Carlo seeds are repetitions of the SAME geometry/texture, not new scenes.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
from fsg_geometry import camera_rotation_h, gaze_direction
from fsg_scene import quad, texture, triangulate_objects

SPEC_ID = "FSG1d-fixed-validation-v1"
CASES = ("tilted_holdout", "step_right")
CASE_GAZE = {"tilted_holdout": (-12., 8.), "step_right": (0., 0.)}
SEEDS = (31, 73)
DEFAULT_SPP = {"small": 64, "full": 256}
TEXTURE_OFFSET = 20000
SPEC = {
    "id": SPEC_ID,
    "reference_commit": "edfe1d2",
    "candidate": "FSG1c-fixed-soft-hdr-srgb-v1",
    "cases": list(CASES),
    "tilted_holdout": {"gaze_yaw_pitch_deg": [-12., 8.], "centre_range_m": 2.6,
                       "tilt_deg": -32., "size_m": [3.2, 3.2], "instance": 1},
    "step_right": {"gaze_yaw_pitch_deg": [0., 0.], "background_z_h_m": -3.2,
                   "foreground_z_h_m": -1.8, "foreground_x_interval_m": [0., 1.65],
                   "foreground_height_m": 3.3, "background_size_m": [4.2, 4.2],
                   "foreground_instance": 1, "background_instance": 2},
    "texture": "fsg_scene.texture(instance_id + 20000); fixed for both eyes and seeds",
    "seed_schedule": {"small": [31], "full": [31, 73]},
    "spp": DEFAULT_SPP,
    "vergence_distance_m": 2.0,
    "lighting": "unchanged FSG1 BlenderBackend.prepare lighting/materials",
    "occlusion_core_erosion_px": {"small": 1, "full": 2},
    "occlusion_min_raw_pixels": {"small": 64, "full": 256},
    "occlusion_min_core_pixels": {"small": 32, "full": 128},
    "occlusion_max_core_accepted": 0,
    "interior_targets": {"coverage_min": 0.90, "median_range_max": 0.01, "p95_range_max": 0.03},
    "no_adoption_or_fusion_authorization": True,
}
FROZEN = {'fsg_geometry.py': 'd9537d8ebc23b60c30e957b484d7353c20ca751f2281729d4ea941e2aacecd5d', 'fsg_scene.py': '1f410577c1103e0197a63a77eef3f47e640807b833876dfde296014fc8b3b134', 'fsg_render.py': '681237fa8533b7cc7c351aa8167bceb6c060dd20dddd630af1df21ecec5ff654', 'fsg_stereo.py': 'faebf0f1b3acbfde60b08830a57213bf29c708c3aa274e493ade0042eb0545e9', 'fsg_evaluate.py': 'a5134b8d8537714d3b9cb074ec65e3bb83dc574827db42359ad27e14c1626da3', 'fsg_stereo_hdr.py': '67e2ec4667bcc179b7fc3c111effce896c12b0f481837b05705b5c74731d5de2', 'fsg_hdr_compare.py': '2413d93cea928569106f02923272225b0b5f6e91a0f2342d7b0bba5cc9ee720f', 'fsg_coverage_audit.py': 'eb95257d2078e38445ab7195bbc2b88a96cd4c5be99fa67bd68ed6f7fbfbb0be'}


def spec_digest() -> str:
    return hashlib.sha256(json.dumps(SPEC, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_frozen() -> dict:
    root = Path(__file__).resolve().parent
    actual = {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in FROZEN}
    if actual != FROZEN:
        bad = [name for name in FROZEN if actual[name] != FROZEN[name]]
        raise ValueError("frozen instrument changed: " + ", ".join(bad))
    return actual


def validation_objects(name: str) -> list[dict]:
    if name == "tilted_holdout":
        g = gaze_direction(*CASE_GAZE[name]); rot = camera_rotation_h(g)
        r, up = rot[:, 0], -rot[:, 1]; a = np.radians(-32.)
        return [quad(2.6*g, r*np.cos(a)+g*np.sin(a), up, 3.2, 3.2, 1, "heldout_tilt")]
    if name == "step_right":
        return [quad([0.,0.,-3.2], [1.,0.,0.], [0.,1.,0.], 4.2,4.2, 2, "heldout_background"),
                quad([.825,0.,-1.8], [1.,0.,0.], [0.,1.,0.], 1.65,3.3, 1, "heldout_foreground_right")]
    raise ValueError("unknown FSG1d case: " + str(name))


def validation_texture(instance: int, size: int = 512) -> np.ndarray:
    return texture(int(instance) + TEXTURE_OFFSET, size)


def validate_mesh(name: str, mesh: dict) -> None:
    """Validate exported quad surfaces, allowing either triangulation diagonal.

    Blender may choose either legal diagonal for a planar quad. Identity, corner
    positions, complete coverage, and absence of duplicate triangles are checked;
    triangle ordering or winding is not a geometric discrepancy.
    """
    wanted = validation_objects(name)
    triangles, ids = mesh["triangles_h"], mesh["instance_ids"]
    if triangles.shape != (2*len(wanted),3,3) or ids.shape != (2*len(wanted),):
        raise ValueError("unexpected validation mesh size")
    if set(ids.tolist()) != {obj["instance_id"] for obj in wanted}:
        raise ValueError("unexpected validation object identity")
    for obj in wanted:
        exported = triangles[ids == obj["instance_id"]]
        if len(exported) != 2:
            raise ValueError("expected two triangles per validation quad")
        corners = np.asarray(obj["vertices_h"])
        distance = np.linalg.norm(exported[:,:,None,:]-corners[None,None,:,:], axis=-1)
        nearest = np.argmin(distance, axis=-1)
        if np.max(np.min(distance, axis=-1)) > 2e-5:
            raise ValueError("exported Blender mesh disagrees with frozen validation specification")
        actual = {tuple(sorted(row.tolist())) for row in nearest}
        if actual not in ({(0,1,2),(0,2,3)}, {(0,1,3),(1,2,3)}):
            raise ValueError("exported triangles do not cover the prescribed quad exactly once")
