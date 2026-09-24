# Bridge-5 checks

Required before execution:

```bash
.venv/bin/python tools/fsg_geometry.py --self-test
.venv/bin/python tools/dev/check_fsg_tangent_frame.py
.venv/bin/python tools/dev/check_fsg_blend_bridge.py
.venv/bin/python tools/fsg_bridge2_select.py --self-test
.venv/bin/python tools/dev/check_fsg_bridge2_select.py
.venv/bin/python tools/fsg_bridge3_fattening.py --self-test
.venv/bin/python tools/dev/check_fsg_bridge3_fattening.py
.venv/bin/python tools/fsg_bridge4_synthetic.py --self-test
.venv/bin/python tools/fsg_bridge4_analyze.py --self-test
.venv/bin/python tools/dev/check_fsg_bridge4.py
.venv/bin/python tools/fsg_bridge5_factorial.py --self-test
.venv/bin/python tools/fsg_bridge5_analyze.py --self-test
.venv/bin/python tools/dev/check_fsg_bridge5.py
```

Package invariants:

- far base depth = 2.40 m;
- slant levels = 0.0 and 1.8;
- far texture gains = 1.0 and 0.44;
- seeds = 2111, 2112, 2113;
- 12 conditions total;
- instance masks identical across all conditions;
- capture threshold alpha = 0.5;
- `tools/fsg_stereo.py` unchanged;
- truth only under `evaluation_only/` and only read after stereo.
