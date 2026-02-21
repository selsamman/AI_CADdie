# Constraints Scene Format (LLM-facing) – v0.2

This document describes the **LLM-facing** scene format (`scene_constraints.json`) that is compiled into the internal `scene.json`.

The goal is to keep the LLM's output **small, repetitive, and selectable** (choose from known tokens/handles) while the compiler and geometry engine remain deterministic.

See `docs/requirements.md` section 5 for the governing principles that apply to all scene authoring, including the mandatory positioning and dependency-order rules.

---

## 1. Files

- Schema: `schemas/scene_constraints/scene_constraints.schema.json`
- Compiler: `engine/constraints.py`
- Feature catalog + resolver: `engine/features.py`

---

## 2. Feature handles

A feature handle is a string of the form:

`ObjectId.feature`

Examples:

- `Octagon.wall:West`
- `Octagon.vertex:North`
- `NewHearth.face:front`
- `HearthSleeper.start`

Feature handles are validated at runtime against the feature catalog (see section 4). References to unknown objects or non-existent features are compile-time errors.

---

## 3. Tokens

Directions (plan): `N NE E SE S SW W NW`

Axes: `N-S`, `E-W`, `NE-SW`, `NW-SE`

---

## 4. Feature catalog

The feature catalog is the authoritative list of valid feature handles for a given scene state. It is built incrementally as objects are defined — after each object is added its features become available for use by subsequent objects.

**The LLM must treat the catalog as sequential and ordered.** An object may only reference features of objects defined earlier in the scene. This is enforced at compile time.

**The catalog is the sole source of truth for valid feature handles.** The LLM must query `engine/features.py` after defining each object to obtain the current catalog rather than relying on any static enumeration. This applies equally to standard prototypes and irregular poly_extrude objects with named edges.

### 4.1 Named edges on irregular poly_extrude objects

A `poly_extrude` object whose geometry cannot be fully described by its standard prototype features may declare named edges in its definition. Named edges are specified as a `named_edges` map from a chosen name to a pair of vertex indices (zero-based, matching the `points` array order):

```json
{
  "id": "OldHearth",
  "prototype": "poly_extrude",
  "params": {
    "points": [...],
    "named_edges": {
      "south_face": [7, 0],
      "chimney_face": [2, 3]
    }
  }
}
```

Named edges are then available as feature handles for subsequent objects:

- `OldHearth.edge:south_face`
- `OldHearth.edge:chimney_face`

Objects that do not publish any relevant named features cannot be used as positioning references by other objects. This is enforced at compile time.

---

## 5. Constraint vocabulary (implemented)

### 5.1 `offset_from_feature`

Positions an origin relative to a named feature on a previously defined object.

```json
{
  "kind": "offset_from_feature",
  "feature": "NewHearth.face:front",
  "dir": "S",
  "offset_in": 2
}
```

### 5.2 `span_between_hits`

Defines an extent between two features along the member axis.

```json
{
  "kind": "span_between_hits",
  "from": "Octagon.wall:West",
  "to": "Octagon.wall:East"
}
```

### 5.3 `point_on_edge_from_vertex`

Positions an origin at a measured distance along a named edge, starting from a named vertex.

```json
{
  "kind": "point_on_edge_from_vertex",
  "edge": "Octagon.wall:NorthEast",
  "vertex": "Octagon.vertex:North",
  "distance_in": 49
}
```

### 5.4 `ray_hit`

Defines an extent by firing a ray from the origin in a given direction until it hits a named feature. The member is trimmed flush to the hit surface.

```json
{
  "kind": "ray_hit",
  "dir": "SW",
  "until": "HearthSleeper.centerline"
}
```

### 5.5 `placement_constraints` for `dim_lumber_member`

All four constraint kinds above are composed inside a `placement_constraints` block:

```json
"placement_constraints": {
  "axis": "E-W",
  "origin": { "...offset_from_feature or point_on_edge_from_vertex..." },
  "extent": { "...span_between_hits or ray_hit..." }
}
```

The compiler expands this into internal numeric placement: `start`, `direction`, `length`.

---

## 6. Example: Hearth Sleeper

English:

> The Hearth Sleeper is positioned 2 inches south of the front face of the New Hearth and extends to the East Wall and the West Wall.

Constraints form:

```json
{
  "id": "HearthSleeper",
  "prototype": "dim_lumber_member",
  "params": {
    "profile": { "id": "1x2.5_actual" },
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

---

## 7. Example: Wing Sleeper (diagonal, ray_hit)

English:

> The Right Wing Sleeper's north side starts at the point on the North East Wall 49 inches from the North Vertex and extends south west ending where it intersects with the Hearth Sleeper.

Constraints form:

```json
{
  "id": "RightWingSleeper",
  "prototype": "dim_lumber_member",
  "params": {
    "profile": { "id": "1x2.5_actual" },
    "placement_constraints": {
      "axis": "NE-SW",
      "origin": {
        "kind": "point_on_edge_from_vertex",
        "edge": "Octagon.wall:NorthEast",
        "vertex": "Octagon.vertex:North",
        "distance_in": 49
      },
      "extent": {
        "kind": "ray_hit",
        "dir": "SW",
        "until": "HearthSleeper.centerline"
      }
    }
  }
}
```

---

## 8. What's next

Planned additions (not yet implemented):

- `distribute_evenly_between` wired into constraints format (operator exists in engine but not yet exposed as a constraint kind)
- `unresolved` records for safe LLM failure path
- Intersection extents that trim to polygon footprints rather than supporting lines only

Keep the LLM-facing vocabulary small, add capabilities one at a time, and cover each with fixtures and tests before considering promoted.
