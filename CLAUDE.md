# Working agreement

Engineering-first project. A visual result at every step. Mistakes are expected, so
this process optimises for cheap recovery rather than for prevention.

## The loop

    Luiz sets direction  →  Chat thinks, writes, runs, shows  →  Luiz runs what needs
    the GPU or real assets  →  Luiz decides  →  repeat

Chat has a sandbox with Blender as a Python module (CPU, no GPU, no large assets, no
network to asset sites). So Chat writes the code and runs it there before handing it
over; what comes back to Luiz has already executed at least once. Some sessions have no
`bpy` at all (Phase B's first did): then Chat says so, runs what is pure numpy, exercises
the Blender-side script through a stub, and the first real run is on the workstation.

Claude Code enters only when a job is too big for a chat turn: a multi-file refactor,
a long run, a large sweep. No specification relay, no review levels, no PR gate.
Push to main; revert if wrong.

Chat calls the handoff. When a conversation's context stops being reconstructible
from this repository, Chat says so, writes whatever is missing into `docs/log.md`,
and prepares the instructions to carry over. A new conversation starts by cloning
and reading, never from a summary: a summary is a second source of truth and starts
drifting immediately.

## Two hard rules

1. **Measured or assumed, never in between.** Every number in a claim is either
   something that was run — say where — or an estimate — say so.
2. **Every tool ships a check that can fail.** A control, a known answer, an
   invariant. A tool that cannot come out wrong has not been tested.

## Conventions

- Metres. The head is fixed; eyes rotate about their own centres.
- `EYE` is a Blender camera object: local −Z is gaze, local +Y is head up.
- Equirect (u, v) → EYE-frame direction: `lon = (u−0.5)·2π`, `lat = (0.5−v)·π`, v = 0 at the top row.
- Sample record: origin, direction, value, footprint (solid angle), ray distance,
  fixation id, raster index.
- Python: plain and typed where it helps. No framework.
- **Two interpreters, and they are not interchangeable.** Scripts run by `blender -b -P`
  use Blender's bundled Python: bpy, mathutils and numpy, nothing else. Host-side scripts
  (`inspect_preview.py`, `check_foveated.py`) use `.venv` and may import OpenEXR or PIL.
  A Blender-side script that imports either is broken on the workstation even if it runs in
  the Chat sandbox, where one interpreter happens to have both. To read an image back
  inside Blender, write single-layer EXR and use `bpy.data.images.load` (rows are bottom-up;
  multilayer cannot be read back this way).
- `blender -b -P` exits 0 even when the script raised. Any Blender-side tool that produces
  an artifact must catch its own failure and exit nonzero.
- Git: forward only. Revert, don't rewrite.

## Cost classes

The project's own renders are fast; a fixation is a fraction of a second. What is slow is
the uniform reference at foveal spacing, which is the baseline foveation replaces. So the
loop never waits on it. Every command falls in one class, and the class decides when it runs:

- **Interactive** — under 10 s. The loop: a fixation, a check, a small sweep. Where
  development lives.
- **Batch** — under 5 min, run while doing something else: a noise floor, a fixation
  sequence, an E₂ sweep.
- **Overnight** — anything longer. Scheduled, justified in one sentence in `docs/log.md`
  before it runs, and its result kept as a pinned asset. References, and a final
  error-versus-budget curve at full scale. Nothing else.

Two habits make the first class real:

- **Build on `--profile small`, report on `--profile full`.** The two profiles in
  `bl_common.PROFILES` are one flag apart: `small` (s₀ = 0.1°, reference 3600x1800 at 1024
  spp, fixations at 64 spp) renders its reference in about a minute; `full` (s₀ = 0.05°,
  7200x3600 at 8192 spp, fixations at 256 spp) is the reported configuration. Geometry, the
  sample record and every check are identical between them. A tool is developed and debugged
  on `small` and run on `full` once, for the number that goes in a note.
- **References are assets, not steps.** A reference is rendered once per scene and profile,
  recorded in `scenes/manifest.json` with its md5, and kept — backed up outside the checkout,
  since `previews/` is gitignored. It is regenerated only if the scene, s₀ or spp changes,
  never to refresh it. This is the one exception to "if a command made it, the command is the
  artifact": here the command is 35 minutes, so the file is the artifact and the md5 proves
  it is the one the log describes.

## Files

- `README.md` — what this is, how to run it, the roadmap, where things stand.
- `DECISIONS.md` — one short block per decision, including what would overturn it.
- `docs/log.md` — dated entries of a few lines: what was run, what came out.
  Anything learned only inside a chat is lost; it goes here.

## Regenerable artifacts are not committed

Renders, previews, and .blend files produced by a script are gitignored. If a command
made it, the command is the artifact. Downloaded scenes are recorded in
`scenes/manifest.json` with source, license and checksum, and are not stored in git.
