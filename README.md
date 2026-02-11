# DescriptiveCAD v0.2 Bootstrap (minimal)

This ZIP establishes the repo structure and contracts:

- `registry/` lists available prototypes and operators.
- `schemas/` contains JSON Schema for prototype params and operator invocations.
- `engine/` contains a tiny Python runner that reads `scene.json` and emits `out.scad`.

**NOTE:** `clip_to_object` is currently a placeholder (no polygon clipping yet).
The purpose of this bootstrap is to lock down taxonomy + file layout first.
