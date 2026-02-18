# Overview
This document specifies the current experimental workflow, constraints, and components for the
AICaddie project.

This is intentionally scoped to browser-based AI assistants that support:
- file upload
- sandbox file I/O
- Python execution
- downloadable artifacts

(Tested conceptually with ChatGPT browser UI and Gemini browser UI.)

---

## 1. Goal

This goal is achieved via a **two-stage** representation:

- An **LLM-facing constraints scene** (`scene_constraints.json`) with a small, token-based vocabulary.
- A deterministic compiler that expands constraints into the internal numeric `scene.json` used by the geometry engine.

See `docs/design.md` and `docs/constraints_format.md`.


Enable a user to:

1. Upload a ZIP bundle containing (this repo):
   - a small deterministic geometry engine
   - operator definitions
   - schemas and instructions
2. Upload a human-readable design specification
3. In a single AI chat session:
   - resolve ambiguities
   - generate a canonical machine-readable scene description as defined in 
     docs/constraints_format.md
   - Convert that to a scene
   - execute a geometry pipeline
   - receive a generated OpenSCAD file

The user never runs a local command line tool.

All execution happens inside the AI sandbox.

This is an experimental, non-commercial workflow.

---

## 2. High-level architecture

AI session responsibilities:

- read instruction.md from the uploaded bundle
- read the user design specification
- identify ambiguities and propose spec patches
- generate a canonical scene description (scene.json)
- write scene.json to the sandbox filesystem
- invoke the geometry engine
- return generated artifacts to the user

Python geometry engine responsibilities:

- read scene.json
- perform deterministic geometry computation
- generate OpenSCAD output
- perform validation / invariants

The AI session must never directly compute geometry.

---

## 3. Scope limitations

This project is explicitly limited to:

- browser-based ChatGPT
- browser-based Gemini

Grok is currently excluded due to lack of reliable ZIP ingestion.

External URL fetching is considered unreliable and must not be required.

All instructions and assets must be contained inside the uploaded ZIP bundle.

---

## 4. Execution environment assumptions

The sandbox environment provided by the assistant supports:

- reading files from the uploaded ZIP
- writing files
- running Python
- returning files as downloadable artifacts

Absolute filesystem paths must not be assumed.

Instructions must refer only to filenames and relative paths.

---

## 5. Core design principle

The system is boxed into three strictly separated concepts:

1. Operation template (schema)
2. Operation instance (scene.json)
3. Operation handler (Python)

No geometry logic may be embedded ad-hoc into the generation pipeline.

If functionality is missing, a new operation must be introduced.

---

## 6. Canonical scene representation

A canonical scene description file named:

scene.json

is the only input to the geometry engine.

The scene file contains:

- room definition
- object prototypes
- object instances
- ordered operator invocations

The scene file is produced by the AI session.

---

## 7. Geometry backend requirements

The geometry backend:

- must be deterministic
- must be written in pure Python (stdlib only)
- must not rely on third‑party binary extensions
- must be portable into browser sandbox environments

Optional acceleration layers (e.g. shapely, pyclipper) may be added later but must not be required.

---

## 8. Current geometry capabilities (v0.1)

The following primitive capabilities are required and considered viable in pure Python:

- regular octagon generation
- rectangular member footprint generation
- basic translation and rotation
- even distribution of members along a line or axis
- trimming members by a half‑plane
- clipping members to a convex room boundary
- flush trimming against reference edges

No general polygon boolean operations are required at this stage.

---

## 9. Semantics and vocabulary

The following semantics are considered normative:

- “ends where it intersects”
  → extend in the given direction until first contact with the referenced boundary or member
  → trim flush to the contacted face

- “trimmed to that intersection”
  → the resulting footprint end face coincides with the contacted boundary

- all geometric directions are in plan view unless explicitly stated otherwise

- X axis = east
- Y axis = north
- Z axis = up
- Z = 0 is the sunken room floor

---

## 10. Operator system

Operators are named operations applied in sequence.

Each operator has:

- a template (schema)
- inputs (object references)
- parameters
- outputs (object references or prefixes)

Example operators already identified:

- distribute_linear_array
- clip_by_halfplane

Operators must be deterministic and side-effect free.

---

## 11. Promotion model

Two tiers of operators exist:

User extension operators:
- may be created ad-hoc
- may be used without tests
- are user responsibility

Promoted/core operators:
- must include minimal tests or invariants
- must be stable and documented
- become part of the shared bundle

Tests are required for promotion, not for prototyping.

---

## 12. Field-driven evolution loop

When the generated geometry is incorrect:

The correction must result in exactly one of:

- a specification patch
- a handler change
- a new operator introduction

Ad-hoc geometry fixes in the pipeline are forbidden.

---

## 13. End-to-end execution protocol

The instruction.md file inside the bundle must define an explicit protocol such as:

1. Read a reference scene.json file from the bundle (for tests), or generate a new one.
2. Write scene.json to the sandbox.
3. Run the engine.
4. Return the generated SCAD file as a downloadable artifact.
5. Do not inline large outputs.

---

## 14. First end‑to‑end validation test

The first required test is purely mechanical:

- copy examples/sample_scene.json to scene.json
- run the engine
- return result.scad

No spec parsing is involved.


---

End of specification.
