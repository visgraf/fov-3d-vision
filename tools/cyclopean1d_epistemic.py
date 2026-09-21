"""Pure helpers for Cyclopean-1d epistemic shoreline refinement.

The module separates image/instance observation from valid stereo depth.  It
contains no Blender, scene, truth or controller dependency.
"""
from __future__ import annotations
from dataclasses import dataclass
import math
import numpy as np

STATE_CODE = {
    "NEVER_OBSERVED": 1,
    "OBSERVED_TARGET_NO_DEPTH": 2,
    "OBSERVED_TARGET_WITH_DEPTH": 3,
    "OBSERVED_NONTARGET_ONLY": 4,
    "MIXED_OBSERVATION": 5,
    "NO_RANGE_REFERENCE": 6,
}
CODE_STATE = {v: k for k, v in STATE_CODE.items()}


@dataclass(frozen=True)
class ProjectedEvidence:
    target_seen: int = 0
    target_depth_valid: int = 0
    nontarget_seen: int = 0
    nontarget_depth_valid: int = 0
    supported_projections: int = 0


def classify_counts(e: ProjectedEvidence, has_range_reference: bool = True) -> str:
    if not has_range_reference:
        return "NO_RANGE_REFERENCE"
    if e.target_seen > 0 and e.nontarget_seen > 0:
        return "MIXED_OBSERVATION"
    if e.target_seen > 0:
        return "OBSERVED_TARGET_WITH_DEPTH" if e.target_depth_valid > 0 else "OBSERVED_TARGET_NO_DEPTH"
    if e.nontarget_seen > 0:
        return "OBSERVED_NONTARGET_ONLY"
    return "NEVER_OBSERVED"


def project_head_to_rectified_core(calibration: dict, rectification: dict, xyz_h: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Project head-frame points into the saved left rectified core.

    This reproduces the geometry used by the frozen stereo path: original left
    camera coordinates -> R1 rectification -> P1 projection -> crop offset.
    It does not infer depth; callers supply the 3D continuation-test points.
    """
    q = np.asarray(xyz_h, float).reshape(-1, 3)
    eye = calibration["eyes"][0]
    centre = np.asarray(eye["centre_h_m"], float)
    r_hc = np.asarray(eye["R_hc"], float)
    r1 = np.asarray(rectification["R1"], float)
    p1 = np.asarray(rectification["P1"], float)
    if p1.shape != (3, 4):
        raise ValueError("P1 must be 3x4")
    xyz_c = (q - centre) @ r_hc
    xyz_rect = xyz_c @ r1.T
    h = np.concatenate((xyz_rect, np.ones((len(q), 1), float)), axis=1) @ p1.T
    with np.errstate(divide="ignore", invalid="ignore"):
        uv_full = h[:, :2] / h[:, 2:3]
    x0, y0, _w, _h = map(int, rectification["crop_xywh"])
    uv_core = uv_full - np.array([x0, y0], float)
    front = np.isfinite(uv_core).all(1) & np.isfinite(h[:, 2]) & (h[:, 2] > 0)
    return uv_core, front


def sample_projected_evidence(
    calibration: dict,
    rectification: dict,
    instance_id: np.ndarray,
    valid_depth: np.ndarray,
    raw_support: np.ndarray,
    xyz_h: np.ndarray,
    object_id: int,
) -> list[ProjectedEvidence]:
    ids = np.asarray(instance_id)
    valid = np.asarray(valid_depth, bool)
    support = np.asarray(raw_support, bool)
    if ids.shape != valid.shape or ids.shape != support.shape:
        raise ValueError("saved patch arrays have inconsistent shape")
    uv, front = project_head_to_rectified_core(calibration, rectification, xyz_h)
    out: list[ProjectedEvidence] = []
    h, w = ids.shape
    for k in range(len(uv)):
        if not front[k]:
            out.append(ProjectedEvidence())
            continue
        x = int(np.rint(uv[k, 0])); y = int(np.rint(uv[k, 1]))
        if not (0 <= x < w and 0 <= y < h) or not support[y, x]:
            out.append(ProjectedEvidence())
            continue
        is_target = int(ids[y, x]) == int(object_id)
        is_valid = bool(valid[y, x])
        out.append(ProjectedEvidence(
            target_seen=int(is_target),
            target_depth_valid=int(is_target and is_valid),
            nontarget_seen=int(not is_target),
            nontarget_depth_valid=int((not is_target) and is_valid),
            supported_projections=1,
        ))
    return out


def add_evidence(a: ProjectedEvidence, b: ProjectedEvidence) -> ProjectedEvidence:
    return ProjectedEvidence(
        target_seen=a.target_seen + b.target_seen,
        target_depth_valid=a.target_depth_valid + b.target_depth_valid,
        nontarget_seen=a.nontarget_seen + b.nontarget_seen,
        nontarget_depth_valid=a.nontarget_depth_valid + b.nontarget_depth_valid,
        supported_projections=a.supported_projections + b.supported_projections,
    )


def self_test() -> None:
    cases = [
        (ProjectedEvidence(), True, "NEVER_OBSERVED"),
        (ProjectedEvidence(target_seen=3), True, "OBSERVED_TARGET_NO_DEPTH"),
        (ProjectedEvidence(target_seen=3, target_depth_valid=1), True, "OBSERVED_TARGET_WITH_DEPTH"),
        (ProjectedEvidence(nontarget_seen=2), True, "OBSERVED_NONTARGET_ONLY"),
        (ProjectedEvidence(target_seen=1, nontarget_seen=1), True, "MIXED_OBSERVATION"),
        (ProjectedEvidence(), False, "NO_RANGE_REFERENCE"),
    ]
    for e, has_range, expected in cases:
        got = classify_counts(e, has_range)
        if got != expected:
            raise AssertionError(f"expected {expected}, got {got}")

    # Minimal projection/sampling control: identity camera, 3x4 pinhole matrix,
    # point on optical axis -> centre pixel.  Observation and valid depth are
    # deliberately varied independently.
    c = {"eyes": [{"centre_h_m": [0, 0, 0], "R_hc": np.eye(3).tolist()}]}
    r = {
        "R1": np.eye(3),
        "P1": np.array([[10.,0.,2.,0.],[0.,10.,2.,0.],[0.,0.,1.,0.]]),
        "crop_xywh": np.array([0,0,5,5]),
    }
    ids = np.zeros((5,5), np.int32); ids[2,2] = 141
    valid = np.zeros((5,5), bool)
    support = np.ones((5,5), bool)
    e0 = sample_projected_evidence(c, r, ids, valid, support, np.array([[0.,0.,2.]]), 141)[0]
    if classify_counts(e0) != "OBSERVED_TARGET_NO_DEPTH":
        raise AssertionError("image observation incorrectly required valid depth")
    valid[2,2] = True
    e1 = sample_projected_evidence(c, r, ids, valid, support, np.array([[0.,0.,2.]]), 141)[0]
    if classify_counts(e1) != "OBSERVED_TARGET_WITH_DEPTH":
        raise AssertionError("valid target depth not recognized separately")
    print("[cyclopean1d-epistemic] PASS never_observed=true seen_no_depth=true measured=true mixed=true projection=true")


if __name__ == "__main__":
    self_test()
