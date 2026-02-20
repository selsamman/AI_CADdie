# Testing for Development Process

Run all tests:

```bash
python -m unittest discover -s tests -v
```

The smoke test runs the example scene through `engine/build.py` and asserts an `out.scad` is produced.

## Scene regression cases (human-verified)

As development progresses, we keep sample scenes that generate SCAD outputs for manual
inspection in OpenSCAD.

Generate SCAD for all cases into `/tmp/aicaddie_scene_tests`:

```bash
python -m scene_tests.run_all
```

Customize output directory and/or file pattern:

```bash
python -m scene_tests.run_all --outdir /tmp/aicaddie_scene_tests --pattern "*.scene.json"
```
