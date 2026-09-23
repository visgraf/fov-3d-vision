"""Blender-side scene inspection and reference builder for Demo-Classroom-1.

NEW Demo-Classroom-1 helper. Runs inside Blender (bpy), so it may use nothing
from the host .venv. Two modes:

  --mode inspect    write scene facts for preflight (no render)
  --mode reference  assign a deterministic structural group id to every
                    renderable mesh, then render one equirectangular panorama
                    from EYE with Combined + Depth.Z + Position.XYZ +
                    Object Index.X

The grouping rule is the parent-root partition: every mesh object has exactly
one root reached by walking .parent, ids are 1..N over SORTED root names. It is
chosen over pass_index (162 of 178 meshes are 0 in this scene) and over
collections (their membership overlaps, so they are not a partition). No
Classroom object name is written here.

The panorama is deliberately read back through its WORLD Position pass rather
than through any assumed equirect pixel-to-direction mapping: the host converts
those world points into the established head frame and re-bins them on the
demo's own spherical grid, so no convention is assumed anywhere.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import sys
import traceback

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bl_common import (configure_multilayer_exr, ensure_cycles, find_eye, pin_seed,  # noqa: E402
                       rigid, script_args, setup_device)


def _root(obj):
    r = obj
    while r.parent is not None:
        r = r.parent
    return r


def _renderable_meshes(scene):
    return [o for o in scene.objects if o.type == "MESH" and not o.hide_render]


def _grouping(scene):
    """Deterministic parent-root partition of the renderable meshes."""
    meshes = _renderable_meshes(scene)
    roots = sorted({_root(o).name for o in meshes})
    gid = {name: i + 1 for i, name in enumerate(roots)}
    members = collections.defaultdict(list)
    for o in meshes:
        members[_root(o).name].append(o.name)
    return meshes, roots, gid, members


def _head(scene):
    eye, note = find_eye(scene)
    m = rigid(eye.matrix_world)
    rot = m.to_3x3()
    return eye, note, {
        "head_origin_m": [float(v) for v in m.translation],
        "head_rot3_world_from_local": [[float(rot[i][j]) for j in range(3)] for i in range(3)],
        "eye_note": note,
    }


def inspect(args) -> dict:
    scene = bpy.context.scene
    bpy.context.view_layer.update()
    meshes, roots, gid, members = _grouping(scene)
    eye, note, head = _head(scene)
    pi = collections.Counter(int(o.pass_index) for o in meshes)
    props = collections.Counter()
    for o in meshes:
        for k in o.keys():
            if not k.startswith("_"):
                props[k] += 1
    colls = collections.Counter()
    for o in meshes:
        for c in o.users_collection:
            colls[c.name] += 1
    em = eye.matrix_world.to_euler()
    return {
        "blender": bpy.app.version_string,
        "engine": scene.render.engine,
        "scene_name": scene.name,
        "scenes_present": [s.name for s in bpy.data.scenes],
        "unit_scale": float(scene.unit_settings.scale_length),
        "unit_system": scene.unit_settings.system,
        "active_camera": scene.camera.name if scene.camera else None,
        "eye": {
            "exists": bpy.data.objects.get("EYE") is not None,
            "found_by": note,
            "type": eye.type,
            "location_m": [float(v) for v in eye.matrix_world.translation],
            "euler_deg": [float(math.degrees(a)) for a in em],
            "is_active_camera": bool(scene.camera is eye),
            **head,
        },
        "mesh_total": len([o for o in scene.objects if o.type == "MESH"]),
        "mesh_renderable": len(meshes),
        "pass_index_histogram": {str(k): int(v) for k, v in sorted(pi.items())},
        "pass_index_usable": bool(len(pi) > 1 and pi.most_common(1)[0][1] < 0.5 * len(meshes)),
        "custom_props": {k: int(v) for k, v in props.most_common(10)},
        "collection_membership": {k: int(v) for k, v in colls.most_common(12)},
        "collections_are_partition": bool(sum(colls.values()) == len(meshes)),
        "parent_root_count": len(roots),
        "grouping_rule": "parent-root partition; ids 1..N over sorted root names",
        "largest_groups": [
            {"id": gid[n], "root": n, "members": len(members[n])}
            for n in sorted(roots, key=lambda x: -len(members[x]))[:8]
        ],
    }


def reference(args) -> dict:
    scene = bpy.context.scene
    ensure_cycles(scene)
    backend = setup_device(scene, args.device)
    bpy.context.view_layer.update()
    meshes, roots, gid, members = _grouping(scene)
    eye, note, head = _head(scene)

    for o in meshes:
        o.pass_index = gid[_root(o).name]

    cam_data = bpy.data.cameras.new("DEMOCLASSROOM1")
    cam_data.type, cam_data.panorama_type = "PANO", "EQUIRECTANGULAR"
    cam_data.latitude_min, cam_data.latitude_max = -math.pi / 2, math.pi / 2
    cam_data.longitude_min, cam_data.longitude_max = -math.pi, math.pi
    cam_data.clip_start, cam_data.clip_end = 0.001, 1.0e5
    cam_data.dof.use_dof = False
    cam = bpy.data.objects.new("DEMOCLASSROOM1", cam_data)
    scene.collection.objects.link(cam)
    cam.matrix_world = rigid(eye.matrix_world)
    scene.camera = cam

    r = scene.render
    r.resolution_x, r.resolution_y, r.resolution_percentage = args.width, args.width // 2, 100
    r.film_transparent = r.use_motion_blur = False
    r.use_single_layer = True
    r.use_compositing = r.use_sequencer = False
    for _what in pin_seed(scene):
        pass
    c = scene.cycles
    c.samples, c.seed = args.spp, 0
    c.use_adaptive_sampling = False
    c.time_limit = 0.0

    vl = bpy.context.view_layer
    vl.use_pass_combined = vl.use_pass_z = vl.use_pass_position = vl.use_pass_object_index = True
    configure_multilayer_exr(scene)
    r.filepath = os.path.join(args.out, "reference.exr")
    bpy.ops.render.render(write_still=True)

    return {
        "blender": bpy.app.version_string,
        "engine": scene.render.engine,
        "device": backend,
        "scene_name": scene.name,
        "unit_scale": float(scene.unit_settings.scale_length),
        "width": int(args.width),
        "height": int(args.width // 2),
        "spp": int(args.spp),
        "view_layer": vl.name,
        "exr": "reference.exr",
        "passes": ["Combined", "Depth.Z", "Position.XYZ", "Object Index.X"],
        "grouping_rule": "parent-root partition; ids 1..N over sorted root names",
        "group_count": len(roots),
        "mesh_renderable": len(meshes),
        "groups": [{"id": gid[n], "root": n, "members": len(members[n])} for n in roots],
        **head,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("inspect", "reference"), required=True)
    ap.add_argument("--blend")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=2048)
    ap.add_argument("--spp", type=int, default=128)
    ap.add_argument("--device", default="OPTIX", choices=["OPTIX", "CUDA", "CPU"])
    args = ap.parse_args(script_args())

    if args.blend:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(args.blend))
    args.out = os.path.abspath(args.out)
    os.makedirs(args.out, exist_ok=True)
    rec = inspect(args) if args.mode == "inspect" else reference(args)
    name = "scene_inspect.json" if args.mode == "inspect" else "reference_meta.json"
    with open(os.path.join(args.out, name), "w") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    print(f"[demo-classroom1-scene] {args.mode.upper()}_OK -> {os.path.join(args.out, name)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        if isinstance(exc, SystemExit) and exc.code in (0, None):
            raise
        traceback.print_exc()
        print("[demo-classroom1-scene] FAILED", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
