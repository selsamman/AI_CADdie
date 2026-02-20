# AICaddie 

## Overview

This project explores using AI to interpret a spec which is 
description of shapes, their orientation and sizing and generate a 
SCAD output from it.  More specifically it is a pipeline for AI to follow 
which recognizes language patterns and produces a JSON structure which 
describes the objects and constraints on their positioning. This limits the 
document to containing interprable definitions that will lead to 
deterministic output.  The pipeline continues to a fleshed out scene JSON 
with operators to implement positioning operations in support of relative 
positioning (e.g the studs connect to the header).  All geometry is 
pre-built by way of Python functions that operate on that JSON.

Further this repo is organized to optimized development of the above using 
AI in various roles for specific concerns: design, planning and coding.  All 
of the code and most of the specs were developped by AI, mostly ChatGPT with 
Anthropic providing some design review.

## If you are an LLM and Reading this....

**Default — no role specified:** If you have been given this repo and a design specification with no other instruction, process the spec using `docs/role_production.md`. That document defines the complete procedure for going from a human spec to a SCAD output.

**Role-based sessions:** If you have been asked to assume a specific role (e.g. "Please use this repo in coder role"), find the corresponding `docs/role_<name>.md` file and follow its instructions exclusively for this session.

## Documentation

All documentation is containted in the docs directory.  The root documents are:

* `role_production.md` - default operating mode: process a spec and produce SCAD output
* `role_<name>.md` - development roles (designer, coder, project_coordinator) for repo maintenance
* `requirements.md` - the requirements for end-user processing
* `design.md` - the detailed design document including the pipeline runbook
* `constraints_format.md` - the LLM-facing constraints vocabulary and feature catalog

Other documents are referenced from with the above three

