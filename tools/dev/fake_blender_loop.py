"""Run tools/active_loop.py without Blender on the stub's analytic calibration room (see
fake_blender_pairs.py). Host side (venv). Exercises the loop, the belief, the policies and the
record; NOT the renderer.

    .venv/bin/python tools/dev/fake_blender_loop.py --out /tmp/loop/info --policy info --fixations 20 --profile small
    .venv/bin/python tools/dev/fake_blender_loop.py --out /tmp/loop/targets --policy targets --fixations 20 --profile small --targets /tmp/calib.targets.json
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fake_blender_pairs import Scene, install_stubs, make_targets  # noqa: E402

if __name__ == "__main__":
    argv = sys.argv[1:]
    tpath = argv[argv.index("--targets") + 1] if "--targets" in argv else "/tmp/calib.targets.json"
    T = make_targets(tpath)
    install_stubs(Scene(T), None)
    sys.argv = ["active_loop.py", "--"] + argv
    import active_loop
    active_loop.main()
