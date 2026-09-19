"""FSG1d acquire two NEW calibration geometries, with a frozen stereo instrument.

 blender -b --python-exit-code 1 -P tools/fsg_validation_render.py -- \
   --out previews/fsg1/validation-full-seed31 --profile full --seed 31 --device OPTIX --save-blend

No host OpenCV/Pillow imports. Original sources are untouched. Copied setup and
orchestration have AST guards; only fixture/texture dispatch is different.
"""
from __future__ import annotations
import argparse
import ast
import datetime as dt
import inspect
import os
from pathlib import Path
import sys
import time
import traceback
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsg_render as original
from fsg_geometry import (CV_TO_BLENDER, head_to_world, world_to_head, json_write,
                          make_calibration, pixels, project_h, rays_h)
from fsg_scene import ray_mesh
from fsg_validation_scene import (CASES, CASE_GAZE, SEEDS, DEFAULT_SPP, SPEC,
    validation_objects, validation_texture, validate_mesh, spec_digest, check_frozen)

class ValidationBackend(original.BlenderBackend):
    def prepare(self, case: str, calibration: dict, folder: Path, spp: int) -> dict:
        import bpy
        from mathutils import Matrix
        from bl_common import ensure_cycles, setup_device, make_eye, node_material
        import rig
        bpy.ops.wm.read_factory_settings(use_empty=True)
        s = bpy.context.scene
        ensure_cycles(s)
        self.device = setup_device(s, self.preferred_device)
        if self.device == "CPU" and self.preferred_device != "CPU":
            raise RuntimeError("No requested GPU backend available; use --device CPU explicitly only after reviewing runtime cost")
        s.unit_settings.system = "METRIC"
        s.unit_settings.scale_length = 1.0
        s.render.resolution_x, s.render.resolution_y = calibration["image_size_wh"]
        s.render.resolution_percentage = 100
        s.render.pixel_aspect_x = s.render.pixel_aspect_y = 1.0
        s.render.film_transparent = s.render.use_motion_blur = False
        s.render.use_compositing = s.render.use_sequencer = False
        s.render.use_border = False
        s.render.use_persistent_data = True
        s.cycles.samples = spp
        s.cycles.use_adaptive_sampling = False
        s.cycles.use_denoising = False
        s.cycles.time_limit = 0.0
        s.cycles.pixel_filter_type = "BOX"
        s.cycles.filter_width = 1.0
        im = s.render.image_settings
        if hasattr(im, "media_type"):
            im.media_type = "IMAGE"
        im.file_format = "OPEN_EXR"
        im.color_mode = "RGBA"
        im.color_depth = "32"
        im.exr_codec = "ZIP"
        s.view_settings.view_transform = "Standard"
        s.view_settings.look = "None"
        s.view_settings.exposure = 0.0
        s.view_settings.gamma = 1.0
        world = bpy.data.worlds.new("FSG_WORLD")
        s.world = world
        if world.node_tree is None:
            world.use_nodes = True
        world.node_tree.nodes.clear()
        bg = world.node_tree.nodes.new("ShaderNodeBackground")
        bg.inputs["Color"].default_value = (.7,.7,.7,1)
        bg.inputs["Strength"].default_value = .6
        out = world.node_tree.nodes.new("ShaderNodeOutputWorld")
        world.node_tree.links.new(bg.outputs["Background"],out.inputs["Surface"])
        # Fixed EYE is the map frame, never the current gaze.
        e = make_eye(s, calibration["head_origin_w_m"])
        h = np.eye(4); h[:3,:3] = calibration["head_R_wh"]; h[:3,3] = calibration["head_origin_w_m"]
        e.matrix_world = Matrix(h.tolist())
        self.head = e
        for desc in validation_objects(case):
            mesh = bpy.data.meshes.new(desc["name"])
            xyz_w = head_to_world(calibration, desc["vertices_h"])
            mesh.from_pydata(xyz_w.tolist(), [], [(0,1,2,3)])
            mesh.update()
            uv = mesh.uv_layers.new(name="UVMap")
            for poly in mesh.polygons:
                for li in poly.loop_indices:
                    uv.data[li].uv = desc["uv"][mesh.loops[li].vertex_index].tolist()
            obj = bpy.data.objects.new(desc["name"], mesh)
            s.collection.objects.link(obj)
            obj.pass_index = int(desc["instance_id"])
            obj["fsg_surface"] = True
            a = validation_texture(obj.pass_index)
            image = bpy.data.images.new(desc["name"]+"_texture", width=len(a), height=len(a), alpha=True, float_buffer=True)
            image.colorspace_settings.name = "Non-Color"
            rgba = np.concatenate((a,np.ones((*a.shape[:2],1),np.float32)),axis=-1)
            image.pixels.foreach_set(rgba.ravel())
            image.update(); image.pack()
            mat = node_material(desc["name"]+"_mat")
            tex = mat.node_tree.nodes.new("ShaderNodeTexImage"); tex.image = image
            tex.interpolation = "Linear"; tex.extension = "EXTEND"
            diff = mat.node_tree.nodes.new("ShaderNodeBsdfDiffuse")
            diff.inputs["Roughness"].default_value = 0.0
            output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
            mat.node_tree.links.new(tex.outputs["Color"], diff.inputs["Color"])
            mat.node_tree.links.new(diff.outputs[0], output.inputs["Surface"])
            obj.data.materials.append(mat)
        # Broad area light; all geometry remains opaque and diffuse.
        light_data = bpy.data.lights.new("FSG_KEY", "AREA")
        light_data.energy = 100.; light_data.shape = "DISK"; light_data.size = 3.
        light = bpy.data.objects.new("FSG_KEY",light_data); s.collection.objects.link(light)
        light.matrix_world = Matrix(h.tolist())
        light.location = head_to_world(calibration, np.array([0.,1.,.2])).tolist()
        # Build actual eye rotations through the repository rig, then assert our
        # calibration prescription agrees. No changes to the original rig code.
        from fsg_geometry import gaze_direction
        target_h = gaze_direction(*calibration["gaze_yaw_pitch_deg"])*calibration["prescribed_vergence_distance_m"]
        pair = rig.pair_for_point(head_to_world(calibration,target_h),
                                  np.asarray(calibration["head_origin_w_m"]),
                                  np.asarray(calibration["head_R_wh"]),calibration["ipd_m"])
        self.cameras = []
        for k, eye in enumerate(calibration["eyes"]):
            g = pair["eyes"][k]
            pos, rb = rig.camera_pose(np.asarray(calibration["head_origin_w_m"]),
                                     np.asarray(calibration["head_R_wh"]),
                                     rig.eye_offsets_local(calibration["ipd_m"])[k], g["yaw"], g["pitch"])
            actual_r = np.asarray(calibration["head_R_wh"]).T @ rb @ CV_TO_BLENDER
            if not np.allclose(actual_r, eye["R_hc"], atol=1e-9):
                raise RuntimeError("repository rig and FSG camera conventions disagree")
            if not np.allclose(world_to_head(calibration,pos),eye["centre_h_m"],atol=1e-9):
                raise RuntimeError("head-frame eye centres disagree")
            data = bpy.data.cameras.new("FSG_"+eye["name"])
            data.type = "PERSP"; data.sensor_fit = "HORIZONTAL"; data.sensor_width = 36.
            data.sensor_height = 36.; data.shift_x = data.shift_y = 0.
            data.lens = eye["K"][0][0]*data.sensor_width/calibration["image_size_wh"][0]
            data.clip_start = .01; data.clip_end = 100.
            data.dof.use_dof = False
            cam = bpy.data.objects.new("FSG_"+eye["name"], data); s.collection.objects.link(cam)
            m = np.eye(4); m[:3,:3] = rb; m[:3,3] = pos
            cam.matrix_world = Matrix(m.tolist()); self.cameras.append(cam)
        bpy.context.view_layer.update()
        self.scene = s
        self.mesh = self.export_mesh(calibration)
        self.checks = self.check_geometry(calibration)
        if self.save_blend:
            s.camera = self.cameras[0]
            bpy.ops.wm.save_as_mainfile(filepath=str(folder/"fixture.blend"))
        return self.mesh


def acquire(args: argparse.Namespace, backend) -> dict:
    """Shared production/stub orchestration; never calls stereo or reads its result."""
    out = Path(args.out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output must be new or empty: {out}")
    out.mkdir(parents=True,exist_ok=True)
    t_all = time.perf_counter()
    results = []
    names = CASES if args.case == "all" else (args.case,)
    for ci, name in enumerate(names):
        t_case = time.perf_counter(); folder = out/name; folder.mkdir()
        ev = folder/"evaluation_only"; ev.mkdir()
        c = make_calibration(args.profile,*CASE_GAZE[name])
        mesh = backend.prepare(name,c,folder,args.spp)
        np.savez_compressed(ev/"mesh.npz", **mesh)
        obs = {}; seconds=[]; seeds=[]
        w,h = c["image_size_wh"]; uv = pixels(w,h)
        t_oracle = 0.
        for eye_id, eye in enumerate(c["eyes"]):
            seed = 10000*args.seed + 100*CASES.index(name) + eye_id
            rgb, secs = backend.render_eye(eye_id,c,folder,args.spp,seed)
            if rgb.shape != (h,w,3) or not np.isfinite(rgb).all(): raise RuntimeError("bad RGB buffer")
            obs["rgb_"+eye["name"]] = rgb.astype(np.float32)
            t0 = time.perf_counter()
            oracle = ray_mesh(np.asarray(eye["centre_h_m"]),rays_h(eye,uv),mesh)
            obs["instance_"+eye["name"]] = oracle["instance_id"]
            t_oracle += time.perf_counter()-t0
            seconds.append(secs); seeds.append(seed)
        if seeds[0] == seeds[1]: raise RuntimeError("inter-eye render seeds must differ")
        np.savez_compressed(folder/"observation.npz",**obs)
        json_write(folder/"calibration.json",c)
        data = {"schema":"FSG1-acquisition-v1", "source":backend.source,
                "case":name, "profile":args.profile, "spp":args.spp, "seeds_lr":seeds,
                "profile_default_spp":getattr(args,"profile_default_spp",{"small":64,"full":256}[args.profile]),
                "blender_version":backend.version, "device":backend.device,
                "render_seconds_lr":seconds, "oracle_seconds":t_oracle,
                "case_seconds":time.perf_counter()-t_case,
                "primary_camera_samples":2*w*h*args.spp if backend.source=="blender_cycles" else 0,
                "nominal_camera_samples":2*w*h*args.spp,
                "adaptive_sampling":False, "optics":"pinhole; no DOF/motion blur",
                "segmentation":"oracle first-hit Blender pass_index; pixel centre; not antialiased",
                "checks":backend.checks}
        json_write(folder/"acquisition.json",data)
        results.append(data)
        print(f"[fsg-render] {name} source={backend.source} raster={w}x{h} spp={args.spp} "
              f"primary_samples={data['primary_camera_samples']} render_seconds={sum(seconds):.4f}",flush=True)
    run = {"schema":"FSG1-run-v1", "source":backend.source,"complete":True,
           "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"cases":list(names),
           "profile":args.profile,"spp":args.spp,"seed":args.seed,
           "profile_default_spp":getattr(args,"profile_default_spp",{"small":64,"full":256}[args.profile]),
           "primary_camera_samples":sum(x["primary_camera_samples"] for x in results),
           "total_wall_seconds":time.perf_counter()-t_all}
    json_write(out/"run.json",run)  # completion marker written last, never on failure
    print(f"[fsg-render] COMPLETE {out}",flush=True)
    return run


def check_renderer_equivalence() -> None:
    expected = inspect.getsource(original.BlenderBackend.prepare).replace(
        "case_objects(case)", "validation_objects(case)").replace(
        "texture(obj.pass_index)", "validation_texture(obj.pass_index)")
    import textwrap
    if ast.dump(ast.parse(textwrap.dedent(expected))) != ast.dump(ast.parse(textwrap.dedent(inspect.getsource(ValidationBackend.prepare)))):
        raise ValueError("validation renderer differs beyond fixture and texture substitution")
    if ast.dump(ast.parse(inspect.getsource(original.acquire))) != ast.dump(ast.parse(inspect.getsource(acquire))):
        raise ValueError("validation acquisition orchestration differs from frozen original")


def acquire_validation(args: argparse.Namespace, backend) -> dict:
    frozen = check_frozen(); check_renderer_equivalence()
    if args.seed not in SEEDS or (args.profile == "small" and args.seed != 31):
        raise ValueError("seed/profile combination not in prospective schedule")
    if args.spp != DEFAULT_SPP[args.profile] or args.case != "all":
        raise ValueError("only both prescribed cases at default spp are authorized")
    out = Path(args.out).resolve()
    # The original acquire writes its completion marker last. If subsequent
    # specification validation fails, remove that marker: no completed record.
    run = acquire(args, backend)
    try:
        for name in CASES:
            with np.load(out/name/"evaluation_only"/"mesh.npz", allow_pickle=False) as f:
                mesh = {k:f[k] for k in f.files}
            validate_mesh(name, mesh)
        if check_frozen() != frozen:
            raise ValueError("frozen source changed during acquisition")
        json_write(out/"validation_spec.json", {"spec": SPEC, "sha256": spec_digest(), "frozen_sources": frozen})
        run.update(validation_spec_id=SPEC["id"], validation_spec_sha256=spec_digest())
        json_write(out/"run.json", run)
    except BaseException:
        (out/"run.json").unlink(missing_ok=True)
        raise
    print("[fsg-validation-render] COMPLETE spec=" + spec_digest(), flush=True)
    return run


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True); ap.add_argument("--profile", choices=("small","full"), required=True)
    ap.add_argument("--seed", type=int, choices=SEEDS, required=True)
    ap.add_argument("--device", choices=("OPTIX","CUDA","CPU"), default="OPTIX")
    ap.add_argument("--save-blend", action="store_true")
    args=ap.parse_args(argv)
    args.case="all"; args.spp=DEFAULT_SPP[args.profile]; args.profile_default_spp=args.spp
    return args


def main() -> None:
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else sys.argv[1:]
    args=parse_args(argv)
    from bl_common import PROFILES
    if int(PROFILES[args.profile]["fix_spp"]) != args.spp:
        raise ValueError("repository profile spp changed; no override authorized")
    acquire_validation(args, ValidationBackend(args.device, args.save_blend))


if __name__ == "__main__":
    try: main()
    except BaseException as exc:
        if isinstance(exc, SystemExit) and exc.code in (0,None): raise
        traceback.print_exc(); print("[fsg-validation-render] FAILED", flush=True)
        sys.stdout.flush(); sys.stderr.flush(); os._exit(1)
