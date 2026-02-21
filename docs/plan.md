# Working Plan — DescriptiveCAD / AICaddie (v0.2)
Baseline: repo.zip uploaded 2026-02-21
Canonical production pipeline: docs/design.md §0.3

Status: Contract layer structurally sound.

No registry/schema/resolver/handler mismatches detected.

Focus shifts to contract protection and regression safety.

---

# Phase 1 — Lock contract integrity with automated tests

Goal:
Ensure future changes cannot break registry/schema/compiler alignment.

Tasks:

- [ ] Add registry integrity test:

  Verify:

  - every prototype schema_path exists
  - every prototype resolver imports

  - every operator schema_path exists
  - every operator handler imports

Success criteria:

Test fails immediately if registry becomes inconsistent.

---

- [ ] Add compiler contract test:

Verify:

Compiler supports ONLY operators in registry/operators.json

Compiler supports ONLY prototypes in registry/prototypes.json

Success criteria:

Prevents silent contract drift.

---

# Phase 2 — Minimal canonical regression coverage

Goal:
Ensure deterministic SCAD output from constraints pipeline.

Tasks:

- [ ] Ensure at least one constraints-driven scene test exists for:

  poly_extrude  
  regular_octagon_boundary  
  dim_lumber_member

- [ ] Ensure at least one constraints-driven scene test exists for each operator:

  clip_to_object  
  extend_and_trim_to_object  
  distribute_evenly_between

Success criteria:

scene_tests.run_all remains deterministic.

---

# Phase 3 — Error reporting quality (compiler usability)

Goal:
Ensure constraints compiler errors are actionable.

Tasks:

- [ ] Ensure errors include:

  object id  
  operator name  
  failing handle  
  expected alternatives

Success criteria:

LLM or user can fix input deterministically.

---

# Phase 4 — Optional future architecture work (not required for v0.2 stability)

Only after Phase 1-3 complete:

Optional:

- grouping / aggregation support
- unresolved / deferred constraints support
- performance optimization

---

# Immediate next step

Implement Phase 1 registry integrity test.

This locks the contract.