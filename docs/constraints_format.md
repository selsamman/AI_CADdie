# Constraints Scene Format (LLM-facing) – v0.1

This document describes the **LLM-facing** scene format (`scene_constraints.json`) that is compiled into the internal `scene.json`.

The goal is to keep the LLM’s output **small, repetitive, and selectable** (choose from known tokens/handles) while the compiler and geometry engine remain deterministic.

## 1. Files

- Schema: `schemas/scene_constraints/scene_constraints.schema.json`
- Compiler: `engine/constraints.py`
- Feature catalog + resolver: `engine/features.py`

## 2. Feature handles

A feature handle is a string of the form:

`ObjectId.feature`

Examples:

- `Octagon.wall:West`
- `Octagon.vertex:North`
- `NewHearth.face:front`
- `HearthSleeper.start`

**Important:** valid features are **not** enumerated in JSON Schema. They are validated at runtime against the feature catalog produced by `engine/features.py`.

## 3. Tokens

Directions (plan): `N NE E SE S SW W NW`

Axes: `N-S`, `E-W`, `NE-SW`, `NW-SE`

## 4. Current constraint vocabulary (implemented)

This is an incremental implementation. The following kinds are supported today:

### 4.1 `offset_from_feature`

Positions an origin relative to a feature.

```json
{
  "kind": "offset_from_feature",
  "feature": "NewHearth.face:front",
  "dir": "S",
  "offset_in": 2
}
```

### 4.2 `span_between_hits`

Defines an extent between two features along the member axis.

```json
{
  "kind": "span_between_hits",
  "from": "Octagon.wall:West",
  "to": "Octagon.wall:East"
}
```

### 4.3 `placement_constraints` for `dim_lumber_member`

```json
"placement_constraints": {
  "axis": "E-W",
  "reference_edge": "centerline",
  "origin": { "... offset_from_feature ..." },
  "extent": { "... span_between_hits ..." }
}
```

The compiler expands this into internal numeric placement:

- `start`: `[x, y]`
- `direction`: direction token (e.g. `E`, `NE`, `SW`)
- `length`: inches

If `reference_edge` is provided, `placement.start` is interpreted as lying on that long edge
of the member (in plan), and the engine offsets by half the board width to compute the
centerline placement. Supported values: `centerline`, `left`, `right`, `north`, `south`, `east`, `west`.

## 5. Example: “Hearth Sleeper”

English:

> The Hearth Sleeper is positioned 2 inches south of the front face of the New Hearth and extends to the East Wall and the West Wall.

Constraints form (member object excerpt):

```json
{
  "id": "HearthSleeper",
  "prototype": "dim_lumber_member",
  "params": {
    "profile": { "id": "2x6" },
    "placement_constraints": {
      "axis": "E-W",
      "origin": {
        "kind": "offset_from_feature",
        "feature": "NewHearth.face:front",
        "dir": "S",
        "offset_in": 2
      },
      "extent": {
        "kind": "span_between_hits",
        "from": "Octagon.wall:West",
        "to": "Octagon.wall:East"
      }
    }
  }
}
```

## 6. What’s next

Planned additions (not yet implemented):

- point-on-wall-at-distance-from-vertex
- ray-hit-until-feature (for “extends to …” / “ends where it intersects …”)
- intersection extents that trim to polygons (footprints), not just supporting lines
- `unresolved` records for safe LLM failure

Keep the LLM-facing vocabulary small, add capabilities one at a time, and cover each with fixtures + tests.
