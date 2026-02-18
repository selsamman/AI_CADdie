# DescriptiveCAD / AICaddie – Seed context for next session (hand-off)

Date: 2026-02-13

## Goal of the project
Convert a natural-language drafting spec into a deterministic intermediate JSON (“scene_constraints”) that is easy for an LLM to fill out, then compile it into an internal scene representation that resolves to concrete geometry and emits OpenSCAD (`.scad`).

Key design: **two-layer representation**
- **LLM-facing**: `scene_constraints` (small schema; uses feature handles)
- **Internal**: `scene` with concrete placements/geometry
- Build pipeline: constraints → compile → resolve → emit SCAD

## Repo conventions / workflow
- User uploads repo zip as **ai_caddie.zip** (may be created via simple zip; avoid `git archive` unless committed).
- Assistant returns updated repo as **input.zip**.
- `tmp/` output directory is gitignored; only blessed goldens are committed.

## Current capabilities implemented
### Constraint kinds supported (intended)
- `offset_from_feature`: “2 inches south of NewHearth.front_face”
- `span_between_hits`: “extends to East wall and West wall” (for E–W and diagonals)
- `point_on_edge_from_vertex`: “point on NE wall 49 inches from North vertex”
- `ray_hit`: “run SW until you hit HearthSleeper.footprint”

### Dim lumber placement supported (intended)
- Nominal→actual profiles (e.g., `2x6` or `S4S:2x6` mapping)
- Axis/direction tokens: `N NE E SE S SW W NW`
- Side-based placement via `reference_edge`:
  - global: `north/south/east/west`
  - relative: `left/right`
  - default: `centerline`

### Scene-based regression scaffold
- Cases: `scene_tests/cases/*.scene.json`
- Goldens: `scene_tests/golden/*.scad`
- Runner: `python3 -m scene_tests.run_all`
  - Default compares outputs vs goldens; missing goldens cause failure
  - `--no-compare` generates outputs only
  - `--update-golden` blesses current outputs as goldens
- Outputs: `./tmp/scene_tests_out/` by default (repo-local, not `/tmp`)

## What we are testing in the current scenes
### `hearth_sleeper_constraints.scene.json`
Tests: offset-from-feature + span-to-walls.
Expected: HearthSleeper is a long E–W member placed 2" south of hearth face and spans to West/East walls.

### `hearth_sleeper_north_edge_constraints.scene.json`
Tests: same as above plus `reference_edge="north"` to verify side-based placement shifts centerline correctly.

### `diagonal_member_constraints.scene.json`
Tests: diagonal axis/direction support and basic placement.

### `right_wing_sleeper_constraints.scene.json` (critical)
Tests two things:
1) start point: `point_on_edge_from_vertex` on NE wall at given distance from North vertex
2) end point: `ray_hit` SW until first intersection with `HearthSleeper.footprint`

**Expected behavior**:
- RightWingSleeper should terminate (end face) exactly at the contact point with HearthSleeper footprint edge.
- No gap; no overlap beyond the sleeper. This test is NOT about notching/boolean cutting—just computing the correct length so it *abuts*.

## Known problem at end of session (must fix first)
`right_wing_sleeper_constraints` renders a wing sleeper that does NOT abut the visible HearthSleeper correctly.

High-level likely cause (no code-level details needed for PM):
- The `ray_hit` intersection is being computed against the *wrong representation* of the HearthSleeper footprint (e.g., pre–reference-edge/side shift or otherwise inconsistent with the final placed geometry).
- Therefore the computed endpoint is offset from where the visible sleeper actually is.

Acceptance criteria for the fix:
- In OpenSCAD (with octagon hidden if needed), RightWingSleeper visibly ends exactly on the HearthSleeper edge.

## Immediate next engineering task in new session
1) Reproduce failing geometry in `right_wing_sleeper_constraints.scene.json` with current repo snapshot.
2) Fix `ray_hit` so intersections are computed against the **final resolved footprint** of the target object (HearthSleeper), not a reconstructed/pre-shift proxy.
3) Regenerate SCAD for that case and confirm the abutment.
4) Once visually confirmed, bless goldens:
   - `python3 -m scene_tests.run_all --no-compare`
   - verify in OpenSCAD
   - `python3 -m scene_tests.run_all --update-golden`
   - `python3 -m scene_tests.run_all` should pass

## Optional (later) quality-of-life (NOT priority)
- Preview rendering mode to avoid OpenSCAD “melting” of coplanar faces (render-only epsilon shrink / debug modifiers). Not needed to fix correctness.

## Reseed checklist for new chat
- Upload latest repo as `ai_caddie.zip` (zip working directory; exclude `.git`, `tmp`, `__pycache__`, `*.pyc`).
- Provide screenshot of `right_wing_sleeper_constraints.scad` with octagon hidden if still unclear.




# === ADDENDUM: Authoritative semantic clarifications (2026‑02‑16) ===

This section overrides and clarifies prior instructions where there is any conflict.

## 1. offset_from_feature semantics (FINAL)

When:

    placement_constraints.origin.kind = "offset_from_feature"

The meaning is:

    The distance between the referenced feature and the specified member face
    equals offset_in, measured perpendicular to the feature and in direction dir.

NOT centerline.

NEVER centerline.

The engine MUST compute placement.start such that the specified face satisfies the rule.



## 2. reference_edge semantics (CRITICAL)

If:

    reference_edge is specified

THEN:

    The identity of that edge is intrinsic to the member and MUST be honored.

It refers to the store‑defined orientation of dimensional lumber.

Rotation in the scene DOES NOT change edge identity.

The engine MUST use that exact face.

NEVER substitute nearest face.



## 3. Default face selection when reference_edge NOT provided

If reference_edge is absent:

The engine MUST use:

    The member face nearest to the referenced feature in direction dir.

This must be computed using correct sign logic relative to member normal.



## 4. Parallel‑axis requirement (NEW HARD RULE)

offset_from_feature is ONLY VALID if:

    member axis is parallel to the referenced feature axis.

If not parallel:

The engine MUST:

    raise a deterministic error.

It MUST NOT silently approximate.

It MUST NOT ignore the constraint.



## 5. Error reporting requirement (LLM feedback)

Errors MUST include:

    object id
    origin feature
    member axis
    feature axis
    reason

Example:

    ERROR: HearthSleeper axis NE‑SW is not parallel to NewHearth.face:front axis E‑W.
    offset_from_feature requires parallel axes.

This is required so the LLM can correct itself.



## 6. Negative test support requirement

Scene tests may intentionally produce errors.

Test harness must support:

    expected failure cases

These are considered PASS when correct error occurs.



## 7. Golden SCAD comparison requirement

Golden comparison applies ONLY to successful scenes.

Error scenes must not attempt SCAD comparison.



## 8. Intermediate artifact retention

Compiler must retain intermediate compiled scene representations when possible.

This is required for regression analysis.



## 9. Absolute priority order

If conflict exists, priority order is:

1. This addendum
2. Seed context
3. Inline comments
4. Legacy behavior



## 10. Prime directive

Correct geometry semantics ALWAYS take precedence over legacy compatibility.

NEVER preserve incorrect behavior to avoid breaking goldens.

Goldens must reflect correct geometry.

