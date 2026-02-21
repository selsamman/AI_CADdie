# Working Plan — DescriptiveCAD / AICaddie (v0.2)
Plan last revised: 2026-02-20 13:00 America/New_York (-0500)
Baseline: new repo.zip (uploaded in this chat)
Canonical production pipeline: docs/design.md §0.3 (“Two-stage authoring”)
Dev-only process: TESTING.md (root)

## What changed vs the prior plan (based on your notes + new baseline)
- README.md stays **high-level** (no detailed pipeline steps).
- Production pipeline is **defined only** in docs/design.md §0.3 (and supporting docs/*).
- TESTING.md is **development-only**; it should not be treated as production workflow.
- You’ve already taken a pass at docs; this plan is now about verifying alignment and closing concrete gaps.

---

# Phase 1 — Make the v0.2 contract internally consistent (design ↔ docs ↔ code ↔ registries ↔ schemas)
Goal: Everything that the system *claims* is supported (in design/docs) is actually supported by the shipped code and registries, with no contradictions.
Success criteria:
- docs/design.md §0.3 remains the single “production pipeline” definition.
- docs/constraints_format.md and docs/requirements.md match the shipped schemas + compiler behavior.
- registries (operators/prototypes) match what engine imports/uses and what schemas exist.

## Concrete gaps detected in the new baseline (must resolve)
### Gap A — `dim_lumber_member` is implemented + documented, but not registered
Evidence in repo:
- `engine/constraints.py` explicitly lists `dim_lumber_member` as “Supported (current)” and imports it.
- `docs/constraints_format.md` documents `dim_lumber_member` feature handles (`centerline`, `start`, `end`).
- `schemas/prototypes/dim_lumber_member.schema.json` exists.
- **But** `registry/prototypes.json` currently lists only: `poly_extrude`, `regular_octagon_boundary` (length=2).

Task outcomes (choose one path; implement fully):
- [ ] Path A (likely): **Register `dim_lumber_member`** in `registry/prototypes.json` with schema_path + resolver + features list.
- [ ] Path B (if intentionally removed): remove/disable `dim_lumber_member` consistently:
  - update `engine/constraints.py` supported list/imports,
  - update docs/constraints_format.md (remove dim_lumber_member section),
  - remove schema + prototype module or clearly de-scope.

### Gap B — Feature catalog definitions must agree (registry.features ↔ docs/constraints_format ↔ engine/features.py)
Task outcomes:
- [ ] Verify `engine/features.py` returns the same handles documented in `docs/constraints_format.md` for:
  - `regular_octagon_boundary`
  - `poly_extrude`
  - `dim_lumber_member` (if kept)
- [ ] Where mismatch exists: fix ONE source of truth and sync the others (prefer runtime behavior + registries; docs should describe reality).

### Gap C — “Safe failure mode / unresolved” is described in design (§0.3) but must be explicitly staged
Task outcomes:
- [ ] Confirm the current schema/compiler support for “unresolved” (design mentions it; compiler contains the term).
- [ ] If partially implemented: document the *exact* current behavior (what is allowed, what happens downstream).
- [ ] If not implemented: add a small, explicit milestone statement in docs/design.md or docs/constraints_format.md:
  - “unresolved is planned; current behavior is hard fail with clear errors” OR implement minimal unresolved pass-through.

---

# Phase 2 — Compiler correctness + determinism for constraints → scene
Goal: The constraints compiler is deterministic, fails early with actionable errors, and produces internal `scene.json` that validates against the internal schema.
Success criteria:
- For a fixed `scene_constraints.json`, generated `scene.json` is byte-stable (ordering, float formatting policy if applicable).
- Errors identify: object id, constraint index/path, and the invalid token/handle.

Tasks:
- [ ] Establish determinism rules for compiler output (ordering of objects, operator applications, and any derived lists).
- [ ] Upgrade error messages in `engine/constraints.py` to include:
  - object id
  - which constraint (by index or json-path-ish location)
  - offending handle/token and a short “expected” hint
- [ ] Add negative tests (unit tests) that assert error text contains the above.

---

# Phase 3 — Schema and registry coherence (operators + prototypes)
Goal: Any operator/prototype that appears in registries has: schema + handler/resolver + at least one example scene.
Success criteria:
- `registry/operators.json` entries all have valid schema paths and callable handlers.
- `registry/prototypes.json` entries all have schema paths and callable resolvers.
- Each registry entry has at least one minimal example.

Tasks:
- [ ] Verify each operator in `registry/operators.json`:
  - `clip_to_object`
  - `extend_and_trim_to_object`
  - `distribute_evenly_between`
    has: schema + working handler + at least one constraints-driven example.
- [ ] Verify each prototype in `registry/prototypes.json` has: schema + resolver + features.
- [ ] Fix any orphan schemas or orphan code (schema exists but not registered, or registered but missing schema).

---

# Phase 4 — Examples + regression coverage (development quality gate)
Goal: A small suite of canonical examples covers every operator and prototype with deterministic SCAD output.
Success criteria:
- `python -m scene_tests.run_all` produces stable SCAD for all included cases.
- At least one constraints-first example exists per operator and per prototype.

Tasks:
- [ ] Create/verify minimal `scene_constraints.json` examples for:
  - each operator (at least one)
  - each prototype (at least one)
- [ ] Add/update golden `.scad` outputs for regression inspection.
- [ ] Ensure example naming and placement make it obvious which feature/operator is being exercised.

Note: This is a dev-only gate; it should be referenced from TESTING.md, not framed as production workflow.

---

# Phase 5 — Documentation hardening (no new “bundle” doc; docs stay role-aligned)
Goal: Keep docs minimal but unambiguous; avoid duplicating the pipeline outside design §0.3.
Success criteria:
- docs/design.md §0.3 is the canonical production pipeline.
- Supporting docs are purely “formats/contracts” (constraints_format, requirements), not alternate process docs.
- README remains high-level, pointing to design + format docs.

Tasks:
- [ ] Ensure README.md stays overview-level and points to:
  - docs/design.md (pipeline + architecture)
  - docs/constraints_format.md (LLM-facing contract)
  - docs/requirements.md (principles / constraints)
- [ ] Ensure TESTING.md only covers dev gates (unit tests + regression runs), with no “production pipeline” language.

---

## Immediate next step (planner stance)
Start Phase 1 with **Gap A (dim_lumber_member registration decision)** because it currently creates a three-way contradiction:
docs + compiler + schema say it exists, but the prototype registry says it doesn’t.

(Once that’s resolved, Feature Catalog coherence becomes straightforward to validate.)