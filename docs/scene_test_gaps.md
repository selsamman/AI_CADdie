# Scene Test Gap Analysis

**Baseline:** `repo.zip` uploaded 2026-02-22  
**Design revision:** `docs/design.md` rev6, 2026-02-19

This document identifies specific gaps in the scene test suite — operators, prototypes, features, and geometric/behavioral considerations that are either entirely uncovered or inadequately exercised.

---

## Summary of Current Coverage

| Test case | Operator(s) | Prototypes exercised | Constraint kinds |
|---|---|---|---|
| `hearth_sleeper_constraints` | _(none)_ | all 3 | `offset_from_feature`, `span_between_hits` |
| `hearth_sleeper_north_edge_constraints` | _(none)_ | all 3 | `offset_from_feature` + `reference_edge:'north'` |
| `right_wing_sleeper_constraints` | _(none)_ | all 3 | `point_on_edge_from_vertex`, `ray_hit` (footprint) |
| `diagonal_member_constraints` | _(none)_ | all 3 | _(direct placement, no constraint compiler)_ |
| `clip_to_object_constraints` | `clip_to_object` | all 3 | `offset_from_feature`, `span_between_hits` |
| `extend_and_trim_to_object_constraints` | `extend_and_trim_to_object` | all 3 | direct placement |
| `distribute_evenly_between_constraints` | `distribute_evenly_between` | all 3 | direct placement |

---

## Gap 1 — `clip_to_object` operator: multiple targets (`target_ids` list)

**Status:** Only tested with a single element in `target_ids`.  
**What is not covered:** The operator signature accepts a list; clipping a batch (e.g., all the sleeper copies produced by `distribute_evenly_between`) is the primary real-world use case. There is no test that supplies more than one `target_id`, so a regression in the loop body that only fires for the second-or-later element would not be caught.

---

## Gap 2 — `clip_to_object` operator: target fully outside clip polygon

**Status:** The existing test clips a member that protrudes outside — it ends up partially inside. There is no test where the target's footprint lies entirely outside the clip object.  
**Geometric consideration implied by code:** `clip_convex` with a subject fully outside the clipper should return an empty polygon. The operator would then set `footprint = []`. There is no assertion or error-handling test for this degenerate case, and no test verifying the object is dropped or kept empty rather than crashing downstream SCAD generation.

---

## Gap 3 — `clip_to_object` operator: non-convex (irregular) `poly_extrude` as the clip object

**Status:** The clip object in the only test is always the regular octagon boundary.  
**Geometric consideration:** `engine/geom.clip_convex` explicitly requires a convex clipper polygon. If a `poly_extrude` with a non-convex footprint is used as `clip_object_id` the algorithm silently produces incorrect results. No test exercises this path or verifies that concave clippers are rejected with an error.

---

## Gap 4 — `extend_and_trim_to_object` operator: trim against a non-axis-aligned (diagonal) target face

**Status:** The existing test trims an E–W sleeper against an axis-aligned rectangular post (`Post`, a `poly_extrude` whose left face is vertical). The `source_edge` and `direction` point in cardinal directions.  
**What is not covered:** When `source_edge` is a non-axis-aligned segment (or the target polygon has a diagonal face), the midpoint ray and half-plane clip are computed along a diagonal direction. No test exercises this geometry. Given that diagonal members are a first-class use case in the design, this is a meaningful gap.

---

## Gap 5 — `extend_and_trim_to_object` operator: source shorter than trim target (extend path)

**Status:** The operator's docstring says "v0.2 implementation trims only (it does not extend)" and the existing test confirms the trim direction. But the parameter name is `extend_and_trim_to_object`, implying future extension behavior.  
**Gap:** There is no negative test confirming what happens when the ray does not hit the target (no hit path). The code returns `objects` unchanged on no hit, but this silent no-op is not verified by any assertion. A test that confirms the source footprint is _unchanged_ when the ray misses would lock in this contract.

---

## Gap 6 — `distribute_evenly_between` operator: distribution along a non-horizontal axis (non-E–W line)

**Status:** The only test places anchor objects A (x≈0) and B (x≈100) at the same y, so distribution is purely along the x-axis.  
**What is not covered:** The operator interpolates linearly between the two anchor centroids in 2D; when A and B differ in both x and y (diagonal line), the intermediate positions require correct 2D interpolation. No test covers this. There is also no test for a N–S distribution or diagonal distribution, both of which are real floor-layout scenarios.

---

## Gap 7 — `distribute_evenly_between` operator: anchor-point resolution via `geom.footprint` centroid vs. `params.placement.start`

**Status:** The operator has two centroid-resolution branches: it prefers `params.placement.start` if present, then falls back to footprint centroid. The existing test uses `poly_extrude` objects (no `placement.start`), so only the footprint-centroid branch is exercised.  
**Gap:** The `dim_lumber_member` template object's `placement.start` branch (the first branch in `_anchor_pt`) is never exercised by a test. A regression that breaks it would be invisible.

---

## Gap 8 — `regular_octagon_boundary` prototype: non-zero `origin` and rotated `north_wall_normal`

**Status:** Every test uses `origin: [0,0]` and `north_wall_normal: [0,1]` (canonical upright orientation).  
**What is not covered:** The prototype supports arbitrary origin translation and rotation of the octagon (via `north_wall_normal`). No test verifies that:
- Features (`wall:North`, `vertex:NorthEast`, etc.) resolve to geometrically correct positions when the octagon is translated.
- Wall/vertex features are still correct when the octagon is rotated (i.e., `north_wall_normal` is not `[0,1]`).

The rotation math in `regular_octagon_boundary.resolve` (the `atan2`/`cos`/`sin` transform) and the corresponding feature resolution in `features.py` (`resolve_feature_segment` and `resolve_feature_point`) are both exercised only at zero rotation.

---

## Gap 9 — `poly_extrude` prototype: `face:left` and `face:right` features

**Status:** `features.py` lists `face:front`, `face:back`, `face:left`, `face:right`, `center` for `poly_extrude`. Only `face:front` is referenced as a constraint origin in the tests (`NewHearth.face:front` in hearth and wing sleeper tests).  
**What is not covered:** `face:back`, `face:left`, `face:right`, and `center` are never the basis of a constraint origin or extent. A regression in `resolve_feature_segment` for any of these faces would not be detected.

---

## Gap 10 — `poly_extrude` prototype: named edges (`named_edges` map)

**Status:** `named_edges` is a documented and implemented feature (see `constraints_format.md §4.1`). It allows irregular shapes to publish named feature handles (`OldHearth.edge:south_face`). There is no scene test that defines a `poly_extrude` with `named_edges` and then references one of those handles in a subsequent member's constraints.  
**This is a complete gap:** the named-edge feature of the most general prototype has zero test coverage.

---

## Gap 11 — `dim_lumber_member` prototype: `orientation.wide_face` = `side` / `edge`

**Status:** All tests use the default `wide_face: down` orientation (member lying flat). The code has explicit branches for `wide_face: side/edge` (footprint width becomes the thickness `t`, height becomes `w`).  
**Gap:** No test exercises the on-edge orientation or verifies that the resulting footprint dimensions are swapped correctly.

---

## Gap 12 — `dim_lumber_member` prototype: profile resolution via `profile.system`/`profile.nominal` path

**Status:** Tests use either `profile.id` (shorthand like `"2x6"`) or `profile.actual` (explicit `[t,w]`). The `profile.system` + `profile.nominal` composition path in `_resolve_profile` is never exercised.

---

## Gap 13 — `offset_from_feature` constraint kind: `reference_edge` shift with non-cardinal `axis` (diagonal member)

**Status:** `hearth_sleeper_north_edge_constraints` exercises `reference_edge: 'north'` for an E–W member. The `_shift_origin_for_reference_edge` function has branches for diagonal axes (`NE-SW`, `NW-SE`) that translate local `NE`/`NW`/`SE`/`SW` edge tokens into a shift. No test uses `reference_edge` on a diagonal member.

---

## Gap 14 — `ray_hit` extent: `clip_to_hit_line: false` option

**Status:** The existing `right_wing_sleeper_constraints` test uses `ray_hit` with the default `clip_to_hit_line: true` behavior (the code path that re-emits the member as a `poly_extrude` clipped flush to the hit edge). There is no test that explicitly sets `clip_to_hit_line: false` and verifies the un-clipped rectangular footprint is used instead.

---

## Gap 15 — `ray_hit` extent: ray-hits a feature segment (not footprint polygon)

**Status:** The `right_wing_sleeper` test fires a ray at `HearthSleeper.footprint` (a polygon feature). `constraints.py` first tries `resolve_feature_segment` and falls back to `resolve_feature_polygon`.  
**Gap:** The segment-first branch is not tested. A test using `ray_hit` with `until: "SomeMember.centerline"` (a `dim_lumber_member`'s `centerline` feature, resolved as a segment) would exercise the segment path directly.

---

## Gap 16 — `span_between_hits` extent: non-parallel or offset feature walls

**Status:** All `span_between_hits` tests use exactly opposite walls of the octagon (`wall:West` / `wall:East`), which are parallel and symmetric through the origin. The compiler uses `line_intersection` to find where the member axis crosses each wall. If the two walls are not parallel to each other (e.g., `wall:NorthWest` and `wall:SouthEast` for a non-canonical axis), the intersection geometry is different. No test covers a `span_between_hits` that uses non-opposite octagon walls or walls of `poly_extrude` objects.

---

## Gap 17 — `point_on_edge_from_vertex` constraint: `distance_in` at boundary values (0 and full edge length)

**Status:** The only test uses `distance_in: 49` on the NorthEast wall, which is well within the wall. The code validates `0 ≤ dist ≤ L` and selects the correct start/end vertex. No test covers distance = 0 (origin placed at the named vertex itself) or distance = L (origin at the far vertex). These boundary cases exercise the vertex-selection logic in the `da`/`db` comparison.

---

## Gap 18 — Compiler feature-handle validation: reference to a later-defined object

**Status:** `constraints_format.md §4` says objects may only reference features of previously-defined objects, and the compiler enforces this. No test verifies that a forward reference is rejected at compile time with a clear error. This is a negative/error path that has no coverage.

---

## Gap 19 — `regular_octagon_boundary`: `wall_height_in` effect on `anchor_top_z` and member `z_base`

**Status:** `hearth_sleeper_constraints` asserts `z_base = 1.0` for `NewHearth` (implying the compiler correctly lifted it by `wall_height`). But `wall_height_in` is present in some tests and absent in others. The assertion in `hearth_sleeper_constraints` is the only check of `z_base` propagation. No test verifies that when `wall_height_in` is absent (defaults to 1.0 in the prototype) vs. explicitly set to a different value, the `anchor_top_z` and all descendant `z_base` values are correct.

---

## Gap 20 — `extend_and_trim_to_object` operator: `source_edge` indices out of range

**Status:** The implementation explicitly validates `source_edge` indices and raises `ValueError`. This error path has no test coverage. A negative test supplying an out-of-range edge index would lock in the error contract.