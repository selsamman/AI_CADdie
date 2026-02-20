# Working Plan — DescriptiveCAD / AICaddie (v0.2)
Plan last revised: 2026-02-19 13:46 America/New_York (-0500)
Design baseline: docs/design.md last revised 2026-02-19 (rev2)
Bundle spec: bundle.md has been intentionally removed. The design.md and actual repo structure are now the only contract.

---

# Phase 1 — Establish the v0.2 Constraints-First Pipeline as the Canonical Workflow
Goal: Make the repository internally consistent around the single intended pipeline:

scene_constraints.json (author input)
→ compile via engine/constraints.py
→ scene.json (internal resolved scene)
→ engine build
→ .scad output

Success criteria:

- The pipeline is clearly documented in README.md and TESTING.md.
- No documentation refers to bundle.md or bundle concepts.
- A new user can execute the full pipeline deterministically from constraints → scad.

Tasks:

- [ ] Remove any remaining references to bundle.md in:
    - README.md
    - docs/
    - seed_context files
    - comments in engine code (if present)

- [ ] Update README.md to explicitly define the v0.2 pipeline:
    - constraints authoring
    - compile step
    - build step
    - test step

- [ ] Update TESTING.md with exact command sequence:
    - validate constraints
    - compile constraints → scene.json
    - run engine → scad
    - run regression tests

- [ ] Verify engine/constraints.py is the single compiler entry point and document its invocation.

---

# Phase 2 — Documentation and Schema Alignment with Actual Engine Behavior
Goal: Ensure all documentation matches what the engine, schemas, and registries actually support.

Success criteria:

- constraints_format.md matches engine/constraints.py capabilities exactly.
- requirements.md reflects actual prototypes and operators.
- schemas validate all shipped examples successfully.

Tasks:

- [ ] Audit and correct docs/constraints_format.md:
    - origins
    - extents
    - operators
    - feature references

- [ ] Audit docs/requirements.md:
    - Remove unsupported features
    - Clarify supported ones

- [ ] Verify schemas:

  schemas/scene_constraints/scene_constraints.schema.json  
  schemas/scene/scene.schema.json

  match runtime expectations.

- [ ] Fix mismatches between schemas and engine if found.

---

# Phase 3 — Regression Coverage for Constraints-Driven Builds
Goal: Ensure deterministic generation of scad from constraints.

Success criteria:

- scene_tests.run_all passes cleanly.
- Each prototype has at least one constraints-based test.

Tasks:

- [ ] Review existing scene_tests cases.

- [ ] Add missing minimal constraints tests for each prototype:
    - regular_octagon_boundary
    - poly_extrude
    - dim_lumber_member

- [ ] Add operator tests if operators exist in registry/operators.json.

- [ ] Confirm golden SCAD files are stable.

---

# Phase 4 — Compiler Robustness and Error Reporting
Goal: Ensure constraints compilation fails safely and informatively.

Success criteria:

- Compiler reports object id and failing constraint.
- Errors identify missing handles, bad operators, or invalid references.

Tasks:

- [ ] Improve error messages in engine/constraints.py where needed.

- [ ] Add unit tests for failure cases:
    - invalid feature handle
    - unknown prototype
    - malformed constraint

---

# Phase 5 — Seed Context Accuracy for Planner/Coder Workflow
Goal: Ensure seed context files correctly describe the real repo.

Success criteria:

- seed_context_for_AI.md accurately describes pipeline and file roles.
- No references to bundle.md remain.

Tasks:

- [ ] Update docs/seed_context_for_AI.md.

- [ ] Ensure file names and workflow instructions are correct.

---

# Phase 6 — Packaging and Deterministic Repo Snapshot
Goal: Enable reliable archive creation for planner/coder workflow.

Success criteria:

- input.zip contains complete reproducible repo.
- No generated artifacts required for rebuild.

Tasks:

- [ ] Verify repo rebuilds cleanly from source only.

- [ ] Document archive creation procedure.

---

# Phase 7 — Future Work (Not required for v0.2 completion)

Optional enhancements:

- feature catalog expansion
- additional operators
- grouping and aggregation support
- performance optimization

---

# Current Focus Recommendation

Active phase: Phase 1

This phase establishes the correct architectural contract now that bundle.md has been removed.

Subsequent phases depend on this alignment.

---

End of Plan