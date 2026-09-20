"""Scene-level scheduling adapter for Stage II / Scene-1a.

The intra-object controller is imported directly from frozen FSG6f.  This module
only remaps one real instance ID at a time onto FSG6f's expected object/background
labels, asks each seeded object what it would do next, and selects among those
already-valid object actions without adding a learned or weighted utility.
"""
from __future__ import annotations
import numpy as np
import scene1a_public as public
import fsg6f_public as frozen_public
import fsg6f_frontier as object_policy


def remap_instance(instance_id: np.ndarray, object_id: int) -> np.ndarray:
    ids=np.asarray(instance_id)
    if int(object_id) not in public.OBJECT_IDS: raise ValueError("unknown Scene-1a object")
    return np.where(ids==int(object_id),frozen_public.OBJECT_ID,frozen_public.BACKGROUND_ID).astype(np.int32)


def remap_observation(obs: dict, object_id: int) -> dict:
    return {"calibration":obs["calibration"],
            "instance_L":remap_instance(obs["instance_L"],object_id),
            "raw_support_L":np.asarray(obs["raw_support_L"],bool),
            "instance_R":remap_instance(obs["instance_R"],object_id),
            "raw_support_R":np.asarray(obs["raw_support_R"],bool)}


def proposal_rank_key(proposal: dict) -> tuple:
    sel=proposal.get("selected")
    if proposal.get("stop") or sel is None: return (float("inf"),float("inf"),int(proposal["object_id"]))
    return (-float(sel["predicted_new_angular_area_deg2"]),-float(sel["frontier_score"]),int(proposal["object_id"]))


def select_proposal(proposals: list[dict]) -> dict:
    live=[p for p in proposals if not p.get("stop",False) and p.get("selected") is not None]
    if not live:
        return {"stop":True,"reason":"scene_complete","selected_object_id":None,"next_gaze_deg":None}
    best=sorted(live,key=proposal_rank_key)[0]
    return {"stop":False,"reason":"continue","selected_object_id":int(best["object_id"]),
            "next_gaze_deg":[float(x) for x in best["selected"]["next_gaze_deg"]],"proposal":best}


def propose_for_object(state: dict, global_visited_gazes_deg: list[tuple[float,float]]) -> dict:
    oid=int(state["object_id"])
    if state.get("map") is None or state.get("last_target_observation") is None:
        raise ValueError("object must be seeded before autonomous scheduling")
    obs=state["last_target_observation"]; hist=[remap_observation(x,oid) for x in state["observation_history"]]
    L=remap_instance(obs["instance_L"],oid); R=remap_instance(obs["instance_R"],oid)
    gaze=tuple(float(x) for x in state["last_target_gaze_deg"])
    d=object_policy.choose_next(gaze[0],gaze[1],obs["calibration"],L,obs["raw_support_L"],R,obs["raw_support_R"],
                                state["map"].xyz_h,global_visited_gazes_deg,hist)
    d=dict(d); d["object_id"]=oid
    if d.get("selected") is not None:
        s=dict(d["selected"]); s["next_gaze_deg"]=[float(s["yaw_deg"]),float(s["pitch_deg"])]; d["selected"]=s
    return d


def choose_scene_action(states: dict[int,dict], global_visited_gazes_deg: list[tuple[float,float]], chooser=propose_for_object) -> dict:
    proposals=[]
    for oid in sorted(public.OBJECT_IDS):
        if oid not in states: raise ValueError("missing seeded object state")
        proposals.append(chooser(states[oid],global_visited_gazes_deg))
    decision=select_proposal(proposals)
    decision["proposals"]=proposals
    decision["scene_scheduler_rule"]="lexicographic_predicted_new_area_then_frontier_score_then_instance_id"
    return decision


def split_visible_object_masks(instance_id: np.ndarray, valid: np.ndarray) -> dict[int,np.ndarray]:
    ids=np.asarray(instance_id); v=np.asarray(valid,bool)
    if ids.shape!=v.shape: raise ValueError("instance/valid shape mismatch")
    return {oid:v&(ids==oid) for oid in public.OBJECT_IDS}


def is_global_repeat(gaze: tuple[float,float], visited: list[tuple[float,float]]) -> bool:
    return any(np.allclose(gaze,g,atol=1e-9) for g in visited)


def self_test() -> None:
    ids=np.array([[201,202],[203,299]],np.int32); v=np.ones((2,2),bool)
    q=remap_instance(ids,202)
    if not np.array_equal(q,np.array([[142,141],[142,142]],np.int32)):
        raise AssertionError("object remap is not one-vs-rest")
    m=split_visible_object_masks(ids,v)
    if [int(m[o].sum()) for o in public.OBJECT_IDS] != [1,1,1]: raise AssertionError("opportunistic splitter lost visible object")
    # Scheduler must follow frozen action value, not object order.
    ps=[{"object_id":201,"stop":False,"selected":{"predicted_new_angular_area_deg2":3.0,"frontier_score":9.0,"next_gaze_deg":[0,0]}},
        {"object_id":202,"stop":False,"selected":{"predicted_new_angular_area_deg2":8.0,"frontier_score":1.0,"next_gaze_deg":[1,0]}},
        {"object_id":203,"stop":False,"selected":{"predicted_new_angular_area_deg2":5.0,"frontier_score":20.0,"next_gaze_deg":[2,0]}}]
    if select_proposal(ps)["selected_object_id"]!=202: raise AssertionError("scene scheduler is not area-first")
    ps[0]["selected"]["predicted_new_angular_area_deg2"]=8.0; ps[0]["selected"]["frontier_score"]=2.0
    if select_proposal(ps)["selected_object_id"]!=201: raise AssertionError("scene scheduler secondary frontier score broken")
    for p in ps: p["stop"]=True; p["selected"]=None
    if select_proposal(ps)["reason"]!="scene_complete": raise AssertionError("scene completion does not require all objects stopped")
    if not is_global_repeat((1.,2.),[(0.,0.),(1.,2.)]) or is_global_repeat((1.,2.),[(0.,0.)]): raise AssertionError("global no-revisit helper broken")
