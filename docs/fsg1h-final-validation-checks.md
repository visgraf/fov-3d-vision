# FSG1h handoff validation

Chat-side validation performed before handoff:

- Four new Python files compile cleanly.
- `fsg_finalh_scene.py` self-test passes.
- `check_fsg_finalh_validation.py` passes and, unlike FSG1g, explicitly evaluates the actual reference geometry before Blender.
- Deterministic corrected reference populations are:
  - small/left raw/core 1024/768, boundary 1920, foreground/background interior 9600/3840;
  - small/right 1024/768, boundary 1792, interiors 9088/4480;
  - full/left 4096/3072, boundary 6912, interiors 39424/15104;
  - full/right 3840/2816, boundary 6656, interiors 37120/17920.
- The new `--negative fixture` control reconstructs the exact FSG1g off-core geometry and exits 1 because the singly-visible reference is empty.
- Candidate wiring is inherited unchanged from FSG1g: `fsg_stereo_supported.compute_once()`, not the endpoint/footprint candidate.
- No Blender/Cycles render was executed by Chat. Numerical stereo validation remains a workstation measurement.

The correction changes fixture geometry only. FSG1g remains preserved as an invalid smoke experiment in repository history and its output paths are not reused.
