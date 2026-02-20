# Production Role — Spec to SCAD

This document defines the procedure for an LLM processing a human design specification and producing a SCAD output. This is the default operating mode when no other role is specified.

## Summary

Read the design spec provided by the user. Author a `scene_constraints.json` file using the constraints vocabulary. Run the pipeline to produce `out.scad`. Return it as a downloadable artifact.

## Prerequisites — Read First

Before authoring any constraints, read:

1. `docs/constraints_format.md` — the complete constraints vocabulary, feature catalog for known prototypes, and worked examples
2. `docs/requirements.md` section 5 — governing principles for positioning and dependency order

## Authoring Loop

Author `scene_constraints.json` incrementally, one object at a time:

1. Read the next object definition from the spec
2. Define the object in `scene_constraints.json` using only prototypes and constraint kinds documented in `docs/constraints_format.md`
3. Run `engine/features.py` against the current scene state to obtain the updated feature catalog
4. Confirm available feature handles before proceeding to the next object
5. Repeat until all objects are defined

Rules:
- Every object must declare positioning by reference to named features of a previously defined object
- No forward references — an object may only reference features of objects already defined above it in the scene
- Do not invent prototypes, constraint kinds, or feature handles not present in `docs/constraints_format.md`
- If a required parameter is missing or ambiguous in the spec, ask for clarification rather than infer

## Pipeline Execution

See `docs/design.md` section 12 (Runbook) for the exact command and expected outputs.

In brief:

```bash
python engine/run.py scene_constraints.json out.scad
```

## Validation and Error Handling

- Feature handle errors are reported by the compiler with the object id and failing handle — correct at the constraints level and re-run
- Do not attempt to fix errors by patching geometry downstream
- Return `out.scad` as a downloadable artifact only after a clean run

## Status

**This document is a placeholder.** The full authoring loop instructions, including handling of edge cases, ambiguity resolution, and iterative correction, are an implementation task to be developed and tested against the sample spec. See `docs/requirements.md` section 16 for the requirements that these instructions must satisfy.
