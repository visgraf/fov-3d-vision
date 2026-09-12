# Log

Newest last. A few lines per entry: what was run, what came out, what it changed.
Numbers get a "measured" or "assumed" label.

## 2026-09-12 — step 1 tooling written and exercised on CPU

Wrote `tools/` (calibration-room generator, HDRI scene wrapper, 360° preview, inspector,
Poly Haven fetcher). All of it ran in the Chat sandbox against Blender 5.2.1 as a Python
module, CPU only.

Measured, in that sandbox:
- Calibration room preview at 1024×512, 24 spp: 64 s; hole fraction 0, backface fraction 0;
  nadir and zenith depth both 1.600 m, which matches the 1.6 m eye height and the 3.2 m ceiling.
- HDRI path against a synthetic panorama: column shift 0 px, median relative error 0.34 %.
  Negative control, eye rotated 90°: shift 128 px = W/4, as expected.
- Backface detector positive control, one wall's normals flipped: 11.0 % of the sphere.

Learned about Blender 5.2, all measured:
- Multilayer EXR writes one part per pass by default; a reader that looks only at part 0
  sees just Combined. `use_exr_interleave = True` puts them back in one part.
- The equirect camera's depth pass is ray distance from the eye centre, matching |P − c|
  to 3e-7 m. Background reads 1e10.
- The Normal pass flips back-facing normals toward the camera, so it cannot detect
  back-faces. A Backfacing-emission override pass can.

Not tested: the OptiX path, the live Poly Haven API, any real demo file.

## 2026-09-12 — step A1 completed on the GPU (Claude Code, `w3d-scenes`)

All three tiers run on an RTX 4090 through OptiX at 2048x1024, 1.3-5.2 s each. Full numbers
in `scenes/manifest.json`; the three open items from the handover are now closed.

Measured:
- Calibration room: hole fraction 0, backface fraction 0, nadir and zenith 1.60019 m. The
  contact sheet matches the CPU reference structurally, and re-running reproduces
  `report.json` field for field.
- HDRI `workshop` (Poly Haven, CC0, 8k, md5 verified on download): column shift 0,
  rel_err_median 0.0152. Negative control on this machine: 512 px = W/4.
- Classroom (CC0, Christophe Seux): hole fraction 0.0208 (window panes only), backface
  fraction 0.0038, nadir 1.20014 m against a chosen 1.2 m eye height. From the file's own
  shot camera instead, backface fraction was 0.136 - the camera sits 0.46 m off the rear
  wall and sees its back side. Moving the eye into the room is a 36x reduction.

Two findings worth keeping:
- `rel_err_median` has a floor set by the reconstruction filter, not by the mapping or by
  sample count: 16 -> 512 spp moves it 0.0152 -> 0.0154, while a box filter gives 0.0032.
  This matters beyond the identity check, because the footprint omega that travels with each
  sample only means "the average over this solid angle" under a box filter.
- `rotation_euler` does not reach `matrix_world` until the depsgraph runs. Anything that
  repositions the eye must call `bpy.context.view_layer.update()` first, or the old pose is
  silently rendered.

## 2026-09-12 — merged into `fov-3d-vision`

`w3d-scenes` folded in as step A1 (D6). The six handover tools came back byte-identical, so
the only new code was `tools/place_eye.py`. Two changes made while merging, both from the
findings above and both re-run on CPU in the sandbox:
- `preview360.py` gained `--filter` / `--filter-width`, defaulting to Cycles' own filter and
  to width 1.0 for BOX, and records both in `meta.json`. Measured on the synthetic panorama:
  rel_err_median 0.0034 with the default filter, 0.0018 with `--filter BOX`.
- `preview360.py` calls `view_layer.update()` before reading the eye pose.
