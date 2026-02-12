# Testing

Run all tests:

```bash
python -m unittest discover -s tests -v
```

The smoke test runs the example scene through `engine/build.py` and asserts an `out.scad` is produced.

## Scene regression cases (human-verified)

As development progresses, we keep sample scenes that generate SCAD outputs for manual
inspection in OpenSCAD.

Generate SCAD for all cases and compare against committed golden `.scad` files:

```bash
python3 -m scene_tests.run_all
```

Generate outputs only (no compare):

```bash
python3 -m scene_tests.run_all --no-compare
```

After you have verified the generated `.scad` outputs in OpenSCAD, bless/update goldens:

```bash
python3 -m scene_tests.run_all --update-golden
```

Customize output directory and/or file pattern:

```bash
python3 -m scene_tests.run_all --outdir ./tmp/scene_tests_out --pattern "*.scene.json"
```
