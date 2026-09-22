"""Pure structural checks with genuine source-mutation negatives for MultiObject-3b."""
from __future__ import annotations
import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "tools" / "multiobject3b_public.py"
SEED = ROOT / "tools" / "multiobject3b_seed.py"
RUN = ROOT / "tools" / "multiobject3b_run.py"


def _source(p: Path) -> str:
    return p.read_text()


def _checks(pub: str, seed: str, run: str) -> list[tuple[str, bool]]:
    ast.parse(pub); ast.parse(seed); ast.parse(run)
    return [
        (
            "parent_selection_and_scene_ids_consumed_not_handpicked",
            'selected_id = int(pm["selected_object_id"])' in run
            and 'existing_ids = tuple(int(x) for x in pm["instantiated_object_ids"])' in run
            and "selected_object_id = 145" not in (pub + seed + run)
            and "EXISTING_OBJECT_IDS" not in (pub + seed + run),
        ),
        (
            "complete_updated_valid_depth_seed_reuses_rule",
            'mask = valid & (ids == oid)' in seed
            and "select_prescribed_seed(xyz, grid_deg)" in seed
            and "old_history._all_cases(old_scene, om)" in run
            and "new_history._all_cases(growth, gm)" in run
            and "complete updated MultiObject-3a evidence scope" in pub,
        ),
        (
            "one_new_global_fixation",
            "MAX_ADDED_FIXATIONS = 1" in pub
            and 'global_step = int(max(steps) + 1)' in run
            and '"added_fixations": 1' in run
            and '"parent_fixations_rerendered": 0' in run,
        ),
        (
            "generic_scene_renderer_not_legacy_cap",
            'SCENE_RENDERER = "tools/scene_render_fix.py"' in pub
            and '"-P", public.SCENE_RENDERER' in run
            and "reality2_render_fix.py" not in run,
        ),
        (
            "existing_objects_read_only_separate_seed",
            '"read_only": True' in run
            and 'target = np.asarray(rec["valid"], bool) & (np.asarray(rec["instance_id"]) == selected_id)' in run
            and '"existing_objects_read_only": True' in run
            and '"fusion_iterations_added": 0' in run,
        ),
        (
            "growth_revisit_and_scheduler_deferred",
            '"growth_iterations_added": 0' in run
            and '"automatic_scene_scheduler": False' in run
            and '"revisit_scheduler_used": False' in run
            and "No growth" in pub
            and "revisit" in pub,
        ),
    ]


def _mutate(name: str, pub: str, seed: str, run: str):
    if name == "handpick":
        run = run.replace('selected_id = int(pm["selected_object_id"])', 'selected_id = 145', 1)
    elif name == "oldhistoryonly":
        run = run.replace('new_cases = new_history._all_cases(growth, gm)', 'new_cases = []', 1)
    elif name == "visibleonly":
        seed = seed.replace('mask = valid & (ids == oid)', 'mask = (ids == oid)', 1)
    elif name == "multiprobe":
        pub = pub.replace("MAX_ADDED_FIXATIONS = 1", "MAX_ADDED_FIXATIONS = 2", 1)
        run = run.replace('"added_fixations": 1', '"added_fixations": 2', 1)
    elif name == "legacyrenderer":
        pub = pub.replace('SCENE_RENDERER = "tools/scene_render_fix.py"', 'SCENE_RENDERER = "tools/reality2_render_fix.py"', 1)
    elif name == "crossfuse":
        run = run.replace('"fusion_iterations_added": 0', '"fusion_iterations_added": 1', 1)
    elif name == "grow":
        run = run.replace('"growth_iterations_added": 0', '"growth_iterations_added": 1', 1)
        pub = pub.replace("No growth", "Growth", 1)
    else:
        raise SystemExit(f"unknown negative: {name}")
    return pub, seed, run


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--negative"); a = ap.parse_args()
    pub, seed, run = _source(PUB), _source(SEED), _source(RUN)
    base = _checks(pub, seed, run)
    if a.negative:
        mp, ms, mr = _mutate(a.negative, pub, seed, run)
        changed = _checks(mp, ms, mr)
        detected = [n for (n, before), (_, after) in zip(base, changed) if before and not after]
        if not detected:
            print(f"[multiobject3b-negative] ERROR {a.negative} mutation escaped detection")
            raise SystemExit(2)
        print(f"[multiobject3b-negative] PASS {a.negative} detected_by={','.join(detected)}")
        raise SystemExit(1)
    failed = [n for n, ok in base if not ok]
    print("[multiobject3b-seed] " + ("PASS" if not failed else "FAIL") + " parent_selected=true updated_valid_depth_seed=true one_fixation=true separate_entity=true")
    print("[multiobject3b-progress] " + ("PASS" if not failed else "FAIL") + " existing_objects_read_only=true growth=false revisit=false scheduler=false")
    print(f"[multiobject3b-check] SUMMARY passed={len(base)-len(failed)} failed={len(failed)}")
    if failed:
        print("[multiobject3b-check] FAIL " + ",".join(failed))
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
