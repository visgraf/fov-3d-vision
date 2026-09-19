"""Acquire the frozen FSG1h fresh validation suite in Blender.

Reuses the already-checked FSG1d renderer implementation; only its fixture and
texture callbacks, case list and schedule are replaced before acquisition.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import traceback
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsg_validation_render as base
import fsg_finalh_scene as spec
from fsg_geometry import json_write


def configure_base() -> None:
    # ValidationBackend.prepare and acquire resolve these names in the base module.
    # The executable rendering code itself is not copied or changed.
    base.CASES = spec.CASES
    base.CASE_GAZE = spec.CASE_GAZE
    base.validation_objects = spec.final_objects
    base.validation_texture = spec.final_texture


def acquire_final(args: argparse.Namespace) -> dict:
    if args.seed not in spec.SEEDS or (args.profile == "small" and args.seed != spec.SEEDS[0]):
        raise ValueError("seed/profile combination not in FSG1h prospective schedule")
    if args.spp != spec.DEFAULT_SPP[args.profile] or args.case != "all":
        raise ValueError("only the complete prescribed suite at default spp is authorized")
    configure_base()
    # This guard still proves the inherited renderer/acquisition code matches FSG1d.
    base.check_renderer_equivalence()
    out = Path(args.out).resolve()
    run = base.acquire(args, base.ValidationBackend(args.device, args.save_blend))
    try:
        for name in spec.CASES:
            with np.load(out/name/"evaluation_only"/"mesh.npz", allow_pickle=False) as f:
                mesh = {k:f[k] for k in f.files}
            spec.validate_mesh(name, mesh)
        json_write(out/"final_validation_spec.json", {"spec": spec.SPEC, "sha256": spec.spec_digest()})
        run.update(final_validation_spec_id=spec.SPEC_ID,
                   final_validation_spec_sha256=spec.spec_digest())
        json_write(out/"run.json", run)
    except BaseException:
        (out/"run.json").unlink(missing_ok=True)
        raise
    print("[fsg-finalh-render] COMPLETE spec=" + spec.spec_digest(), flush=True)
    return run


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", choices=("small","full"), required=True)
    ap.add_argument("--seed", type=int, choices=spec.SEEDS, required=True)
    ap.add_argument("--device", choices=("OPTIX","CUDA","CPU"), default="OPTIX")
    ap.add_argument("--save-blend", action="store_true")
    args=ap.parse_args(argv)
    args.case="all"; args.spp=spec.DEFAULT_SPP[args.profile]; args.profile_default_spp=args.spp
    return args


def main() -> None:
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]
    args=parse_args(argv)
    from bl_common import PROFILES
    if int(PROFILES[args.profile]["fix_spp"]) != args.spp:
        raise ValueError("repository profile spp changed; no override authorized")
    acquire_final(args)


if __name__ == "__main__":
    try: main()
    except BaseException as exc:
        if isinstance(exc, SystemExit) and exc.code in (0,None): raise
        traceback.print_exc(); print("[fsg-finalh-render] FAILED", flush=True)
        sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
