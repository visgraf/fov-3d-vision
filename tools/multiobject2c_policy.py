"""Pure target-label adapter from the parent-selected scene object to frozen FSG6f.

The scene id is supplied by the completed MultiObject-2b parent.  Geometry,
calibration, support, history, ranking and every FSG6f constant remain unchanged.
Only the instance-label namespace seen by the frozen controller is adapted.
"""
from __future__ import annotations

import numpy as np

import fsg6f_frontier as frozen_policy
import fsg6f_public as frozen_public


def relabel_instances(instance_id: np.ndarray, target_object_id: int) -> np.ndarray:
    ids = np.asarray(instance_id)
    out = np.zeros(ids.shape, dtype=ids.dtype)
    out[ids == int(target_object_id)] = frozen_public.OBJECT_ID
    return out


def history_entry(calibration: dict,
                  instance_L: np.ndarray, raw_support_L: np.ndarray,
                  instance_R: np.ndarray, raw_support_R: np.ndarray,
                  target_object_id: int) -> dict:
    return {
        "calibration": calibration,
        "instance_L": relabel_instances(instance_L, target_object_id),
        "raw_support_L": np.asarray(raw_support_L, bool).copy(),
        "instance_R": relabel_instances(instance_R, target_object_id),
        "raw_support_R": np.asarray(raw_support_R, bool).copy(),
    }


def choose_next(current_yaw_deg: float, current_pitch_deg: float, calibration: dict,
                instance_L: np.ndarray, raw_support_L: np.ndarray,
                instance_R: np.ndarray, raw_support_R: np.ndarray,
                map_xyz_h: np.ndarray, visited_gazes_deg: list[tuple[float, float]],
                observation_history: list[dict], target_object_id: int) -> dict:
    """Call frozen FSG6f with only the parent-selected target label adapted."""
    return frozen_policy.choose_next(
        current_yaw_deg, current_pitch_deg, calibration,
        relabel_instances(instance_L, target_object_id), raw_support_L,
        relabel_instances(instance_R, target_object_id), raw_support_R,
        map_xyz_h, visited_gazes_deg, observation_history,
    )
