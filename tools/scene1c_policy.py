"""Frozen policy adapter for Stage II / Scene-1c.

Scene-1c introduces no runtime attention rule.  It imports Scene-1b's settled
least-served scheduler, which itself imports the frozen FSG6f object controller.
The aliases below exist only so Scene-1c runners have a stage-local module name.
"""
from __future__ import annotations
import scene1c_public as public
import scene1b_public as scheduler_public
import scene1b_policy as frozen_scene_scheduler

if tuple(public.OBJECT_IDS) != tuple(scheduler_public.OBJECT_IDS):
    raise RuntimeError("Scene-1c object IDs drifted from frozen Scene-1b scheduler")
if public.PER_OBJECT_MAX_FIXATIONS != scheduler_public.PER_OBJECT_MAX_FIXATIONS:
    raise RuntimeError("Scene-1c per-object budget drifted from Scene-1b")
if public.MAX_SCENE_FIXATIONS != scheduler_public.MAX_SCENE_FIXATIONS:
    raise RuntimeError("Scene-1c scene budget drifted from Scene-1b")

remap_instance = frozen_scene_scheduler.remap_instance
remap_observation = frozen_scene_scheduler.remap_observation
proposal_rank_key = frozen_scene_scheduler.proposal_rank_key
select_proposal = frozen_scene_scheduler.select_proposal
propose_for_object = frozen_scene_scheduler.propose_for_object
choose_scene_action = frozen_scene_scheduler.choose_scene_action
split_visible_object_masks = frozen_scene_scheduler.split_visible_object_masks
is_global_repeat = frozen_scene_scheduler.is_global_repeat


def self_test() -> None:
    frozen_scene_scheduler.self_test()
