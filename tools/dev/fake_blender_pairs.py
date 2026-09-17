"""Run tools/fixation_pairs.py without Blender: stub bpy / bl_common / render_foveated with an
analytic ray caster over the calibration room's cards and walls, writing real uncompressed EXRs.
Host side (venv: numpy, OpenEXR). Exercises the file plumbing, the record and check_pairs.py; NOT the OSL camera or Blender's
matrix composition (the real run's check (a) does that).

    .venv/bin/python tools/dev/fake_blender_pairs.py --out /tmp/pairs --targets /tmp/calib.targets.json [--vergence off] [--profile small]
"""
import json, math, os, sys, time, types
import numpy as np
import OpenEXR

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, os.path.abspath(TOOLS))
import rig, warp  # noqa

ROOM = {"x": (-3.0, 3.0), "y": (-2.5, 5.0), "z": (0.0, 3.2)}
HEAD_ORIGIN = np.array([0.0, 0.0, 1.6])
HEAD = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]])   # make_eye(yaw=0)


def make_targets(path):
    RINGS = [(0.0, 1), (2.5, 4), (6.0, 8), (12.0, 8), (24.0, 8), (40.0, 8)]
    LADDER_AZ = [55.0, 62.0, 69.0, 76.0, 83.0]; LADDER_DIST = [0.5, 0.8, 1.2, 1.8, 2.6]
    WIRE_AZ = [-55.0 - 4.0 * i for i in range(8)]; WIRE_R = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0]
    f, r, u = np.array([0, 1.0, 0]), np.array([1.0, 0, 0]), np.array([0, 0, 1.0])
    T = []
    for e, nn in RINGS:
        size = 1.0 * (1 + e / 4.0)
        for k in range(nn):
            m = 360.0 * k / nn
            d = f * math.cos(math.radians(e)) + (r * math.cos(math.radians(m)) + u * math.sin(math.radians(m))) * math.sin(math.radians(e))
            d /= np.linalg.norm(d)
            T.append({"name": f"ring_e{e:g}_m{m:g}", "kind": "ring", "e_deg": e, "meridian_deg": m, "distance_m": 2.0, "size_deg": size, "dir_world": d.tolist()})
    for az, dist in zip(LADDER_AZ, LADDER_DIST):
        d = [math.sin(math.radians(az)), math.cos(math.radians(az)), 0.0]
        T.append({"name": f"ladder_{dist:g}m", "kind": "ladder", "azimuth_deg": az, "distance_m": dist, "size_deg": 3.0, "dir_world": d})
    for az, rad in zip(WIRE_AZ, WIRE_R):
        T.append({"name": f"wire_{rad:g}mm", "kind": "wire", "azimuth_deg": az, "distance_m": 1.5, "radius_mm": rad})
    json.dump({"eye_position_m": HEAD_ORIGIN.tolist(), "primary_forward": [0, 1, 0], "up": [0, 0, 1], "alpha0_deg": 1.0, "e2t_deg": 4.0, "targets": T}, open(path, "w"), indent=1)
    return T


class Scene:
    def __init__(self, targets):
        self.cards = []
        for t in targets:
            if "dir_world" not in t:
                continue
            d = np.array(t["dir_world"]); c = HEAD_ORIGIN + d * t["distance_m"]
            half = t["distance_m"] * math.tan(math.radians(t["size_deg"]) / 2)
            nrm = -d                                   # faces the head
            up_c = np.array([0, 0, 1.0]); right_c = np.cross(nrm, up_c); right_c /= np.linalg.norm(right_c)
            up_c = np.cross(right_c, nrm)
            self.cards.append((c, nrm, right_c, up_c, half))

    def cast(self, o, D):
        """o (3,), D (M,3) unit -> (pos (M,3), dist (M,), rgb (M,3)); walls first, cards nearer win."""
        M = len(D)
        t_best = np.full(M, np.inf)
        # box walls
        for ax in range(3):
            for v in ROOM["xyz"[ax]]:
                dd = D[:, ax]
                with np.errstate(divide="ignore", invalid="ignore"):
                    t = (v - o[ax]) / dd
                ok = (t > 1e-6) & np.isfinite(t)
                t_best = np.where(ok & (t < t_best), t, t_best)
        on_card = np.zeros(M, bool)
        for c, nrm, rc, uc, half in self.cards:
            dn = D @ nrm
            with np.errstate(divide="ignore", invalid="ignore"):
                t = ((c - o) @ nrm) / dn
            hp = o[None, :] + t[:, None] * D
            rel = hp - c
            ok = (t > 1e-6) & np.isfinite(t) & (np.abs(rel @ rc) <= half) & (np.abs(rel @ uc) <= half)
            nearer = ok & (t < t_best)
            t_best = np.where(nearer, t, t_best); on_card |= nearer
        pos = o[None, :] + t_best[:, None] * D
        # non-periodic value noise at three scales (a periodic checker makes every matcher
        # ambiguous and says nothing about the plumbing): hashed cell values, positive
        def vnoise(k):
            c = np.floor(pos * k).astype(np.int64)
            hsh = (c[:, 0] * 73856093) ^ (c[:, 1] * 19349663) ^ (c[:, 2] * 83492791)
            return ((hsh * 2654435761) % 4294967296) / 4294967296.0
        v = 0.3 + 0.4 * vnoise(8.0) + 0.3 * vnoise(40.0)   # 12.5 cm and 2.5 cm cells: 0.29 deg at 5 m, above s_eval
        if os.environ.get("FAKE_BLANK_WALLS"):                # C2: walls without texture, so only the cards are matchable
            v = np.where(on_card, v, 0.6)
        rgb = v[:, None] * np.array([[1.0, 0.9, 0.8]])
        return pos, t_best, rgb


def install_stubs(scene_geom, n_holder):
    bpy = types.ModuleType("bpy")
    bpy.ops = types.SimpleNamespace(wm=types.SimpleNamespace(open_mainfile=lambda filepath: None))
    bpy.context = types.SimpleNamespace(scene=types.SimpleNamespace(name="Scene", cycles=types.SimpleNamespace(seed=0, samples=64)),
                                        view_layer=types.SimpleNamespace(update=lambda: None))
    bpy.data = types.SimpleNamespace(filepath="/fake/calib_room.blend")
    bpy.app = types.SimpleNamespace(version_string="fake 5.2.1")
    sys.modules["bpy"] = bpy

    blc = types.ModuleType("bl_common")

    def add_profile(ap, argv, **m):
        ap.add_argument("--profile", choices=["small", "full"], default=None)
        pre = __import__("argparse").ArgumentParser(add_help=False); pre.add_argument("--profile", default=None)
        ch, _ = pre.parse_known_args(argv)
        P = {"small": {"s0": 0.1, "fix_spp": 64}, "full": {"s0": 0.05, "fix_spp": 256}}
        if ch.profile:
            ap.set_defaults(**{d: P[ch.profile][f] for d, f in m.items()})
    blc.add_profile = add_profile
    blc.ensure_cycles = lambda s: None
    blc.setup_device = lambda s, prefer="OPTIX": "FAKE"
    blc.script_args = lambda: sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    class Eye:  # rigid 4x4 as nested list, like mathutils.Matrix indexing
        matrix_world = None
        name = "EYE"
    M = np.eye(4); M[:3, :3] = HEAD; M[:3, 3] = HEAD_ORIGIN
    Eye.matrix_world = M
    blc.find_eye = lambda s: (Eye, "EYE object (fake)")

    class Rig:
        def __init__(self, m): self.m = m; self.translation = m[:3, 3]
        def __getitem__(self, i): return self.m[i]
    blc.rigid = lambda m: Rig(np.array(m))
    blc.eye_record = lambda e: {"object": "EYE", "position_m": HEAD_ORIGIN.tolist(), "forward": (HEAD @ [0, 0, -1.0]).tolist(),
                                "up": (HEAD @ [0, 1.0, 0]).tolist(), "quat_wxyz": [1, 0, 0, 0]}
    sys.modules["bl_common"] = blc

    rf = types.ModuleType("render_foveated")
    rf.HERE = os.path.abspath(TOOLS)
    state = {}

    def setup_foveated_camera(scene, eye, shader, e2, emax, n, spp, exr_codec="ZIP"):
        state.update(e2=e2, emax=emax, n=n, rs=warp.raster_samples(n, e2, emax)); return "CAM"

    def set_gaze(cam, eye, yaw, pitch, offset_local=(0, 0, 0)):
        pos, rot = rig.camera_pose(HEAD_ORIGIN, HEAD, offset_local, yaw, pitch)
        state.update(pos=pos, rot=rot, yaw=yaw, pitch=pitch)

    def render_fixation(scene, spp, out_path=None, seed=0):
        t0 = time.perf_counter()
        n = state["n"]; rs = state["rs"]
        dcam = rs["direction_cam"].reshape(-1, 3) * np.array([1, 1, -1.0])   # camera local (-Z fwd)
        dw = dcam @ state["rot"].T
        pos, dist, rgb = scene_geom.cast(state["pos"], dw)
        inside = rs["inside"].reshape(-1)
        dist = np.where(inside, dist, 1e10); pos = np.where(inside[:, None], pos, 0.0); rgb = np.where(inside[:, None], rgb, 0.0)
        # independent noise per render (a seed shared between the two eyes correlates their noise
        # and a matcher then matches the noise pattern; measured on the stub, 2026-09-15)
        state["count"] = state.get("count", 0) + 1
        rgb = rgb + np.random.default_rng(seed * 100003 + state["count"]).normal(0, 0.01, rgb.shape)
        state["frame"] = (rgb.reshape(n, n, 3).astype(np.float32), dist.reshape(n, n).astype(np.float32), pos.reshape(n, n, 3).astype(np.float32))
        return time.perf_counter() - t0

    def save_render_result(scene, out_path):
        rgb, z, pos = state["frame"]
        chans = {"ViewLayer.Combined.R": rgb[..., 0], "ViewLayer.Combined.G": rgb[..., 1], "ViewLayer.Combined.B": rgb[..., 2],
                 "ViewLayer.Combined.A": np.ones_like(z), "ViewLayer.Depth.Z": z,
                 "ViewLayer.Position.X": pos[..., 0], "ViewLayer.Position.Y": pos[..., 1], "ViewLayer.Position.Z": pos[..., 2]}
        header = {"compression": OpenEXR.NO_COMPRESSION, "type": OpenEXR.scanlineimage}
        OpenEXR.File(header, {k: np.ascontiguousarray(v) for k, v in chans.items()}).write(out_path)

    def fixation_meta(scene, eye, eye_note, cam, backend, n, s0, e2, emax, spp, yaw, pitch, seconds, profile, seconds_include_write):
        r = state["rot"]
        return {"blend": "/fake", "scene": "Scene", "fov_kind": "calib", "blender": "fake", "eye": blc.eye_record(None), "eye_note": eye_note,
                "profile": profile, "gaze_yaw_deg": yaw, "gaze_pitch_deg": pitch,
                "camera_position_m": state["pos"].round(6).tolist(), "camera_forward": (r @ [0, 0, -1.0]).round(6).tolist(),
                "camera_right": (r @ [1.0, 0, 0]).round(6).tolist(), "camera_up": (r @ [0, 1.0, 0]).round(6).tolist(),
                "warp": {"E2_deg": e2, "e_max_deg": emax, "s0_deg": s0, "raster": n}, "spp": spp, "seed": 0, "device": backend,
                "render_seconds": round(seconds, 4)}
    rf.setup_foveated_camera = setup_foveated_camera; rf.set_gaze = set_gaze; rf.render_fixation = render_fixation
    rf.save_render_result = save_render_result; rf.fixation_meta = fixation_meta
    sys.modules["render_foveated"] = rf


if __name__ == "__main__":
    argv = sys.argv[1:]
    tpath = argv[argv.index("--targets") + 1]
    T = make_targets(tpath)
    install_stubs(Scene(T), None)
    sys.argv = ["fixation_pairs.py", "--"] + argv
    import fixation_pairs
    fixation_pairs.main()
