# Working agreement

Engineering-first project. A visual result at every step. Mistakes are expected, so
this process optimises for cheap recovery rather than for prevention.

## The loop

    Luiz sets direction  →  Chat thinks, writes, runs, shows  →  Luiz runs what needs
    the GPU or real assets  →  Luiz decides  →  repeat

Chat has a sandbox with Blender as a Python module (CPU, no GPU, no large assets, no
network to asset sites). So Chat writes the code and runs it there before handing it
over; what comes back to Luiz has already executed at least once.

Claude Code enters only when a job is too big for a chat turn: a multi-file refactor,
a long run, a large sweep. No specification relay, no review levels, no PR gate.
Push to main; revert if wrong.

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
- Python: plain and typed where it helps. numpy, bpy, OpenEXR. No framework.
- Git: forward only. Revert, don't rewrite.

## Files

- `README.md` — what this is, how to run it, the roadmap, where things stand.
- `DECISIONS.md` — one short block per decision, including what would overturn it.
- `docs/log.md` — dated entries of a few lines: what was run, what came out.
  Anything learned only inside a chat is lost; it goes here.

## Regenerable artifacts are not committed

Renders, previews, and .blend files produced by a script are gitignored. If a command
made it, the command is the artifact. Downloaded scenes are recorded in
`scenes/manifest.json` with source, license and checksum, and are not stored in git.
