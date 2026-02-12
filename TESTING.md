# Testing

Run all tests:

```bash
python -m unittest discover -s tests -v
```

The smoke test runs the example scene through `engine/build.py` and asserts an `out.scad` is produced.

## Scene regression cases (golden SCAD)

As development progresses, we keep sample scenes (inputs) and golden SCAD outputs
(expected) to catch regressions.

### Run (generate to ./tmp and compare to goldens)

```bash
python3 -m scene_tests.run_all
```

Generated outputs are written to `./tmp/scene_tests_out/` and compared against
`scene_tests/golden/`.

### Bless current outputs as new goldens

```bash
python3 -m scene_tests.run_all --update-golden
```

### Customize

```bash
python3 -m scene_tests.run_all --outdir scene_tests/scad/aicaddie_scene_tests --pattern "*.scene.json"
```
