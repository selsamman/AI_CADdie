# AICaddie – Experimental In-Chat CAD Stack Specification
Design last revised: 2026-02-19 (rev3)

This document provides a clear taxonomy of the building blocks and how they 
relate. It defines the *shape of the system* and gives small illustrative examples.

This project is intentionally scoped to browser-based AI assistants that support:
- file upload
- sandbox file I/O
- Python execution
- downloadable artifacts

All instructions and assets are contained in this repo and uploaded as a ZIP 
to the LLM for processing described in the requirements.


---

## 0. Pipeline overview

The full pipeline from human spec to OpenSCAD output is three stages:

1. **LLM authors `scene_constraints.json`** — reads the human design spec and produces a constraints scene using the token-based vocabulary defined in `docs/constraints_format.md`. No numeric geometry is computed by the LLM.

2. **Compiler produces `scene.json`** (`engine/constraints.py`) — deterministically expands feature handles and constraint kinds into numeric placements. The LLM never touches this file directly.

3. **Geometry engine produces `.scad`** (`engine/run.py`) — reads `scene.json`, executes the operator pipeline, emits OpenSCAD output.

All design artifacts are chained from this document. Key references:
- LLM authoring format and feature catalog: `docs/constraints_format.md`
- Governing principles for positioning and dependency order: `docs/requirements.md` section 5
- Constraint compiler: `engine/constraints.py`
- Feature catalog and runtime validation: `engine/features.py`
- Geometry engine entry point: `engine/run.py`

---

## 0.3 Two-stage authoring (LLM-facing constraints → internal scene)

This project supports a **two-stage** scene description workflow:

1. **LLM-facing constraints scene** (`scene_constraints.json`)
   - Small, token-based vocabulary designed for LLM reliability.
   - Uses **feature handles** (e.g. `Octagon.wall:West`, `NewHearth.face:front`) rather than numeric geometry.
   - Validated against `schemas/scene_constraints/scene_constraints.schema.json`.

2. **Internal scene** (`scene.json`)
   - Existing rich scene schema used by the deterministic geometry engine.
   - All placements are numeric by the time this schema is validated.

A deterministic **compiler** expands constraints → internal scene (see `engine/constraints.py`). The runtime then resolves prototypes/operators as usual and emits OpenSCAD.

### Feature catalog

To avoid hard-coding prototype-specific feature enums into JSON Schema, prototypes publish a runtime **feature catalog**:

- For each object in a (resolved) scene, `engine/features.py` can list supported feature handles.
- The catalog is documented statically in `docs/constraints_format.md` for LLM authoring, and validated at runtime against `engine/features.py`.
- The constraints compiler validates every feature handle against this catalog and fails early with clear errors.

### Safe failure mode (important for LLM authoring)

The constraints format is intentionally designed to support a safe “I can’t resolve this” path (e.g. an `unresolved` entry) rather than forcing hallucinated geometry. This is implemented in stages as the constraint vocabulary expands.

---

## 1. Core concepts

### 1.1 Scene
A Scene is:
- a set of object declarations
- plus an ordered list of operator invocations
- plus an anchor reference used for default feature lookup

The internal scene (`scene.json`) is produced by the compiler from the LLM-authored `scene_constraints.json`. See `docs/constraints_format.md` for the LLM-facing authoring format.

### 1.2 Prototype
A Prototype is a registered “object type” definition that includes:
- a parameter schema (what fields must be provided)
- feature rules (what named edges/vertices/planes can be referenced)
- a resolver (how to turn params into initial geometry, deterministically)

Prototypes live in the repo and are not invented at runtime.

### 1.3 Object instance
An ObjectInstance is a declared thing in a specific scene.
It references a prototype and provides:
- `params` (prototype-specific)
- `pose` (transform)
- optional explicit `geom` if already materialized

### 1.4 Operator
An Operator is a registered transformation that:
- reads objects (by stable IDs)
- may materialize geometry
- may create additional objects (new IDs)
- may write named features (references) for later steps
- must be deterministic

Operators live in the repo and are not invented at runtime.

### 1.5 Resolved scene state
The Python engine executes the operator list in order and maintains an internal “resolved state”:
- authoritative geometry for each object (explicit footprint + extrusion if solid)
- registry of features/references

This internal state may optionally be exported as `scene_resolved.json` for debugging, but is not
required for correctness.

---

## 2. Coordinate system and anchor semantics

### 2.1 Axes
- +X = East
- +Y = North
- +Z = Up
- Z=0 is the sunken room floor unless explicitly overridden.

### 2.2 Anchor
Each scene defines an `anchor_id`.

Default feature references (e.g., “North Wall”) are interpreted as referring to the anchor object’s
features unless explicitly scoped to another object.

The anchor object need not be a “container” in a special sense; it is simply the default reference
frame and feature provider.

---

## 3. Geometry representation (authoritative data model)

### 3.1 Solid geometry (v0.x canonical)
All solid objects are represented as:
- `footprint`: a simple 2D polygon (list of points, ordered)
- `extrusion`: `{ z_base, height }`

This single representation covers rectangles, triangles, quadrilaterals, and irregular footprints
(e.g., masonry/hearth shapes).

### 3.2 Boundary geometry
A boundary/outline object is represented as:
- `footprint`
- optional `wall_height` only for visualization
Boundary objects do not participate as solids unless explicitly extruded.

### 3.3 Materials / style (rendering-only)
- `style: { color: [r,g,b,a] }`
No textures are assumed in v0.x.

---

## 4. Features and references

### 4.1 Generic features
Any polygon footprint has:
- vertices indexed: `v0..v(n-1)`
- edges indexed: `e0..e(n-1)` where `ei` is between `vi` and `v(i+1)`

A feature reference may identify:
- a vertex
- an edge
- an infinite line through an edge
- a half-plane derived from an edge (used for trimming/flush cuts)

### 4.2 Named features
Prototypes may define named features.
Example: `regular_octagon_anchor` defines:
- walls: `NorthWall, NorthEastWall, ..., NorthWestWall`
- vertices: `NorthVertex, NorthEastVertex, ..., NorthWestVertex`

Non-canned shapes may define named features via explicit mapping:
- “surface name” → “edge between two points” (or an edge index)

---

## 5. Operators: result patterns

An operator may produce results in three ways:

1) **Modify**: replace geometry of an existing object ID
2) **Emit**: create new objects with new IDs
3) **Annotate**: create named references/features usable by later operators

Offcut geometry, if produced, must be tagged:
- `tags: ["debug"]`
and excluded from export by default unless explicitly requested.

---

## 6. Scene JSON: shape and examples

### 6.1 Top-level scene structure (illustrative)

```json
{
  "schema_version": "0.2",
  "anchor_id": "room",
  "objects": [
    {
      "id": "room",
      "prototype": "regular_octagon_boundary",
      "params": {
        "span_flat_to_flat_in": 167,
        "origin": [0, 0],
        "north_wall_normal": [0, 1],
        "wall_height_in": 13.75
      },
      "style": { "color": [0.8, 0.8, 0.8, 0.15] }
    },

    {
      "id": "sleeper_A",
      "prototype": "rect_from_edge",
      "params": {
        "start_edge": {
          "on_object": "room",
          "edge": "SouthWall",
          "offset_from_vertex_in": 0
        },
        "length_in": 120,
        "thickness_in": 1.0,
        "width_in": 2.5,
        "direction": "North"
      },
      "extrusion": { "z_base": 0, "height": 1.0 },
      "style": { "color": [1, 1, 1, 1] }
    }
  ],
  "operators": [
    {
      "op": "clip_to_object",
      "target_ids": ["sleeper_A"],
      "clip_object_id": "room"
    }
  ]
}
```

Notes:
- This example mixes explicit `extrusion` with prototype params. v0.x may allow extrusion to be
  provided either as a top-level object field or inside params—pick one when freezing schemas.

### 6.2 Example: distribute then clip then trim (illustrative)

```json
{
  "schema_version": "0.2",
  "anchor_id": "room",
  "objects": [
    { "id": "room", "prototype": "regular_octagon_boundary", "params": { "...": "..." } },
    { "id": "sleeper_proto", "prototype": "rect_from_edge", "params": { "...": "..." }, "extrusion": { "z_base": 0, "height": 1.0 } }
  ],
  "operators": [
    {
      "op": "distribute_linear_array",
      "source_id": "sleeper_proto",
      "out_prefix": "sleeper_mid_",
      "count": 6,
      "spacing_mode": "equal_clear_gap",
      "span_between": {
        "start_ref": { "on_object": "room", "feature": "SouthWestWall" },
        "end_ref":   { "on_object": "room", "feature": "SouthEastWall" }
      }
    },
    {
      "op": "clip_to_object",
      "target_prefix": "sleeper_mid_",
      "clip_object_id": "room"
    },
    {
      "op": "trim_by_halfplane",
      "target_prefix": "sleeper_mid_",
      "halfplane_ref": {
        "on_object": "hearth_sleeper",
        "feature": "north_face_halfplane"
      }
    }
  ]
}
```

The key idea:
- distribute materializes multiple sleepers from one prototype instance
- clip trims them to room boundary
- trim makes flush cuts relative to a referenced face/edge

---

## 7. Prototype registry

The repo contains a registry that maps prototype names to:
- JSON schema for params
- resolver function name (Python)
- named feature rules

Illustrative registry entry:

```json
{
  "name": "regular_octagon_boundary",
  "params_schema": "schemas/prototypes/regular_octagon_boundary.schema.json",
  "resolver": "prototypes.regular_octagon_boundary.resolve",
  "features": ["NorthWall", "NorthEastWall", "...", "NorthVertex", "..."]
}
```

---

## 8. Operator registry

Similarly, operators are registered with:
- JSON schema for op instance
- handler function name (Python)

Illustrative registry entry:

```json
{
  "name": "trim_by_halfplane",
  "params_schema": "schemas/operators/trim_by_halfplane.schema.json",
  "handler": "operators.trim_by_halfplane.apply"
}
```

---

## 9. LLM responsibilities and constraints (v0.x)

The assistant's authoring output is `scene_constraints.json` — the LLM-facing constraints format described in `docs/constraints_format.md`. The assistant never authors `scene.json` directly. The compiler (`engine/constraints.py`) performs that expansion deterministically.

### Incremental authoring loop

The assistant must author `scene_constraints.json` incrementally, one object at a time, using the following loop:

1. Define the next object from the spec in `scene_constraints.json`
2. Run `engine/features.py` against the current scene state to obtain the updated feature catalog
3. Confirm the available feature handles before proceeding
4. Use only handles present in the current catalog when defining subsequent objects
5. Repeat until all objects are defined

This loop ensures the assistant never references a feature that does not exist, and catches errors at the earliest possible point rather than at final compilation.

### The assistant must:
- choose from registered prototypes and constraint kinds only (see `docs/constraints_format.md`)
- fill required fields only — ask for clarification rather than infer missing parameters
- reference only features of previously defined objects (see `docs/requirements.md` section 5)
- produce `scene_constraints.json` that validates against `schemas/scene_constraints/scene_constraints.schema.json`
- run the compiler to validate the complete constraints file before returning output; correct any errors at the constraints level

The assistant must not:
- invent new prototypes, operators, or constraint kinds not documented in `docs/constraints_format.md`
- invent geometry parameters not present in the user's spec
- compute numeric geometry directly — all geometry is produced by the deterministic Python engine
---

## 10. Grouping / aggregation (future-friendly, minimal hook)

Grouping is supported by allowing a scene to include an inline “group definition” that can be
instantiated with a pose transform.

This is out of scope for v0.2 implementation, but the data model should not preclude:

- `groups`: reusable scene fragments with their own local anchor
- `instantiate_group` operator: applies a rigid transform and emits namespaced object IDs

---
## 11 Design Notes
### How “trim” is implemented

A trim/clip operator does **true footprint geometry**:

- It computes a **new 2D polygon footprint** (list of points).
- It **replaces** the object’s footprint with that new polygon (in the resolved scene state).
- SCAD output is then dumb rendering: `linear_extrude(height) polygon(points)`.

The operator does **not** need to create a “triangle offcut” object. Offcuts may exist only as
optional debug artifacts (tagged) if useful for visualization.

## 12. Runbook — Pipeline Execution

This section defines the exact commands and expected outputs for the constraints-first pipeline. This is the authoritative reference for role instructions and replaces any separate instruction files.

### 12.1 Full pipeline: constraints → SCAD

Single command — compilation and geometry generation are handled internally:

```bash
python engine/run.py scene_constraints.json out.scad
```

`engine/run.py` detects that the input is a constraints scene, runs the compiler automatically, then runs the geometry engine. Returns `out.scad`.

If the input is already a resolved `scene.json` (e.g. for debugging), the compile step is skipped and the engine runs directly.

### 12.2 What validation occurs

Two validation gates fire automatically during the pipeline:

**Feature handle validation** — runs during the compile step (`engine/constraints.py`). Every feature handle in the constraints file is validated against the runtime feature catalog. Invalid object references or non-existent feature names produce an error identifying the object id and the failing handle. This is the primary runtime enforcement mechanism.

**Geometry invariants** — run during the build step. The engine checks geometric consistency of resolved objects before emitting SCAD.

Note: the JSON schema files in `schemas/` are authoring references and LLM guidance only. They are not invoked at runtime. The engine is pure Python stdlib and has no jsonschema dependency.

### 12.3 Run regression tests

```bash
python scene_tests/run_all.py
```

Compares generated SCAD output against golden files in `scene_tests/golden/`. All tests must pass before a constraints or engine change is considered stable.

### 12.4 Expected outputs

- `out.scad` — the generated OpenSCAD file, returned as a downloadable artifact
- Errors are reported to stdout with object id and failing constraint; no partial output is written

