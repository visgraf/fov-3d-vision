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

## 2026-09-12 — step A1 re-run from scratch, all three tiers reproduce

Ran the full run order in `docs/a1-scene-gathering.md` on the Linux box (Blender 5.2.1, OptiX,
RTX 4090), with both downloads fetched again rather than reused. Every number in
`scenes/manifest.json` came back. Nothing in the repository changed as a result, so the manifest
stands as written.

Measured, tier by tier:
- Calib room: `report.json` identical to the previous run **field for field**, and
  `calib_room.targets.json` byte-identical. Render 1.7 s.
- Workshop HDRI: re-downloaded (339.5 MB), md5 matched the committed `asset.json`, and
  `fetch_hdris.py` rewrote `asset.json` byte-identically (`git status` clean). column_shift 0,
  rel_err_median 0.015172, p99 0.228632 against 0.01517 / 0.22863 in the manifest. Box-filter
  diagnostic: 0.003232 / 0.047311 against 0.0032 / 0.047. Negative control, eye rotated 90°:
  512 px = W/4. Render 1.4 s at 16 spp.
- Classroom: zip 70,279,690 bytes, md5 3adbb7114b514bfc6fc724ce20f86b4e — now recorded in the
  manifest, which previously pinned this file by URL alone. From `renderCam`, backface_fraction
  0.13598 and depth_min 0.1035 m; renderCam is at y −4.466 against a scene bound at −4.925, so
  the "0.46 m off the rear wall" in the note is 0.459 m measured. From `EYE` at (−0.6, −1.0, 1.2):
  hole 0.020788, backface 0.003776, nadir 1.200143 m, zenith 1.696648 m, against 0.02079 / 0.0038 /
  1.20014 / 1.69665. Render 5.2 s at 64 spp, denoised.

One new thing, and it is the reason `report.json` can be identical while the EXR is not. The
preview `pano.exr` does **not** come back byte-identical: md5 differs run to run. Rendering the
same file twice and comparing channel by channel shows why — Depth.Z and Position are bit-identical
(0 differing pixels), while Combined differs by at most 5.96e-07 and Normal by at most 4.17e-07,
i.e. float32 accumulation order on the GPU. Every quantity `inspect_preview.py` reports is either
geometric or a median over the sphere, so none of them moves. Compare reports, not checksums.
