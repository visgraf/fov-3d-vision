"""Pure label adapter from object 143 to the frozen FSG6f single-object policy.

FSG6f's controller is intentionally left byte-for-byte unchanged.  Its only semantic
assumption about instance identity is equality to fsg6f_public.OBJECT_ID (141).  For
this transfer experiment we present object 143 under that target label and map every
other scene id to zero/non-target.  The adapter does not touch geometry, support,
calibration, history, policy constants, or ranking.
"""
from __future__ import annotations

import numpy as np

import fsg6f_frontier as frozen_policy
import fsg6f_public as frozen_public
import multiobject1b_public as public


def relabel_instances(instance_id: np.ndarray) -> np.ndarray:
    ids = np.asarray(instance_id)
    out = np.zeros(ids.shape, dtype=ids.dtype)
    out[ids == public.OBJECT_ID_2] = frozen_public.OBJECT_ID
    return out


def history_entry(calibration: dict,
                  instance_L: np.ndarray, raw_support_L: np.ndarray,
                  instance_R: np.ndarray, raw_support_R: np.ndarray) -> dict:
    return {
        "calibration": calibration,
        "instance_L": relabel_instances(instance_L),
        "raw_support_L": np.asarray(raw_support_L, bool).copy(),
        "instance_R": relabel_instances(instance_R),
        "raw_support_R": np.asarray(raw_support_R, bool).copy(),
    }


def choose_next(current_yaw_deg: float, current_pitch_deg: float, calibration: dict,
                instance_L: np.ndarray, raw_support_L: np.ndarray,
                instance_R: np.ndarray, raw_support_R: np.ndarray,
                map_xyz_h: np.ndarray, visited_gazes_deg: list[tuple[float, float]],
                observation_history: list[dict]) -> dict:
    """Call the frozen FSG6f policy with only the target-label namespace adapted."""
    return frozen_policy.choose_next(
        current_yaw_deg, current_pitch_deg, calibration,
        relabel_instances(instance_L), raw_support_L,
        relabel_instances(instance_R), raw_support_R,
        map_xyz_h, visited_gazes_deg, observation_history,
    )
