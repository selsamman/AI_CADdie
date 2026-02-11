# DescriptiveCAD (Prototype v0.1)

Prototype pipeline: **canonical Scene IR (JSON)** → deterministic Python build → OpenSCAD.

## Included
- Scene IR schema: `schemas/scene.schema.json`
- Engine: `engine/build.py`
- Example: `examples/sample_scene.json`

## Run example
```bash
python engine/build.py examples/sample_scene.json --out out.scad
```
Open `out.scad` in OpenSCAD.

## Note
This repo does not include the LLM front-end yet. The LLM is expected to produce `scene.json`.
