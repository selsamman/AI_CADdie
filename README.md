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

## If you are an LLM and Reading this....

You are either being asked by abd end-user to accept a spec and work through 
the pipeline to produce a SCAD output as a downloadable file or you are being asked to 
participate in a specific role as a developer.  Depending on how you were 
asked to refer to this repo determines that.  Unless the chat includes 
"You are <role>" please assume the former and follow 
doc/enduser_role.md", otherwise follow docs/<role>_role.md

## Key Documents in doc/

* <role>_role.md - describe the role AI is to play when working with this repo
* requirements.md - the requirements for end-user processing
* design.md - the detailed design document describing internal components
* other documents are referenced from with the above three sets

## Current Status

At present we are working on the constraints definitions that the LLM will
create and all of the downstream pipeline from there that results in a SCAD
Concrete next steps:
*

## Included
- Scene IR schema: `schemas/scene.schema.json`
- Engine: `engine/build.py`
- Example: `examples/sample_scene.json`

## Run example
```bash
python engine/build.py examples/sample_scene.json --out out.scad
```
Open `out.scad` in OpenSCAD.

## Note
This repo does not include the LLM front-end yet. The LLM is expected to produce `scene.json`.
