# Working Plan — DescriptiveCAD / AICaddie (v0.2)
Plan last revised: 2026-02-21 12:30 America/New_York (-0500)
Baseline: repo.zip uploaded in this chat
Canonical production pipeline: docs/design.md §0.3 (two-stage authoring)
Dev-only process: docs/TESTING.md

## Planner notes
- README is not a detailed documentation home.
- Production pipeline lives in docs/design.md §0.3.
- Development gates live in docs/TESTING.md.
- This plan should live at docs/plan.md and be the single active plan artifact.

---

# Phase 0 — Confirm “what is canonical” (doc roles and boundaries)
Goal: Make sure each doc has one job, with no duplicated “pipeline” descriptions outside design §0.3.
Success criteria:
- docs/design.md §0.3 is the only place that defines the production pipeline.
- docs/constraints_format.md defines only the constraints contract (schema + semantics), not workflow.
- docs/TESTING.md defines only dev workflows/tests, not production.
- docs/requirements.md defines goals/constraints, not implementation details.

Tasks:
- [ ] Scan docs for any “how to run production pipeline” instructions outside design §0.3 and convert to links/pointers.

---

# Phase 1 — Contract consistency: design ↔ constraints_format ↔ registries ↔ schemas ↔ compiler
Goal: Remove contradictions in the LLM-facing contract so “write constraints → compile → scene → scad” is predictable.
Success criteria:
- Anything the compiler says is “supported” is present in registries and has schemas.
- Anything in registries has a schema and an implementation path.
- constraints_format matches actual compiler behavior and available prototypes/operators.

Tasks:
- [ ] Prototype registry consistency check
  - Ensure every prototype referenced in:
    - docs/constraints_format.md
    - the constraints compiler supported list (if such a list exists)
      is present in `registry/prototypes.json` with correct schema_path and resolver.
  - Ensure there are no “orphan” prototype schemas (schema exists but no registry entry) unless intentionally marked internal/legacy.

- [ ] Operator registry consistency check (constraints-stage operators)
  - Ensure each operator in `registry/operators.json` has:
    - a schema in `schemas/operators/`
    - a compiler implementation path
  - Ensure docs/constraints_format.md operator list matches `registry/operators.json`.

- [ ] Feature handle contract check
  - For each prototype, verify that:
    - docs/constraints_format.md handles == runtime handles produced/accepted (engine/features / prototype code)
  - If there is any mismatch: fix runtime + registry first, then sync docs.

---

# Phase 2 — Lock the contract with automated checks (dev gates)
Goal: Prevent Phase 1 contradictions from creeping back in.
Success criteria:
- A test fails if a registry references a missing schema or non-importable handler/resolver.
- A test fails if constraints compiler advertises support for an operator/prototype not in registries.

Tasks:
- [ ] Add “registry integrity” unit test:
  - All schema paths exist
  - All handlers/resolvers import
- [ ] Add “compiler advertised support ⊆ registries” unit test:
  - supported prototypes subset of registry/prototypes.json
  - supported operators subset of registry/operators.json
- [ ] Add at least two negative constraints compile tests:
  - unknown prototype
  - unknown operator
    and assert error messages include object id + location + expected values hint.

(These are referenced from docs/TESTING.md; not production workflow.)

---

# Phase 3 — Minimal canonical examples + regression scenes (constraints → scad)
Goal: Every constraints operator and prototype has at least one deterministic example and golden output.
Success criteria:
- For each operator in `registry/operators.json`, there is at least one constraints-based example that reaches SCAD deterministically.
- For each prototype in `registry/prototypes.json`, there is at least one constraints-based example.
- `scene_tests.run_all` (or equivalent) is the dev gate.

Tasks:
- [ ] Add/verify one minimal constraints example per operator
- [ ] Add/verify one minimal constraints example per prototype
- [ ] Ensure golden SCAD stability rules are documented (ordering/naming/floats) in docs/TESTING.md

---

# Phase 4 — “Unresolved / safe failure mode” (only after contract is clean)
Goal: Align design §0.3’s stated behavior with implementation.
Success criteria:
- Docs state exactly what happens today (hard fail vs unresolved pass-through).
- If unresolved is implemented: schema + compiler + tests cover it.

Tasks:
- [ ] Decide: implement minimal unresolved now OR explicitly defer with the exact current behavior documented
- [ ] Add one regression test for the chosen behavior

---

## Immediate priority order
1) Phase 1: registry/schema/compiler/doc consistency (prototypes + operators + feature handles)
2) Phase 2: enforce with tests
3) Phase 3: examples + golden regressions
4) Phase 4: unresolved/safe-failure alignment