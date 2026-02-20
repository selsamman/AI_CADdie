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

Please consider how this repo was presented to you and whether you were 
asked to assume a specific role (e.g. "Please use this repo in coder role"). 
Each role is defined in an md file named <role>.md.  Please find that file 
and strictly follow the instructions there for chat processing.

## Documentation

All documentation is containted in the docs directory.  The root documents are:

* <role>_role.md - describe the role AI is to play when working with this repo
* requirements.md - the requirements for end-user processing
* design.md - the detailed design document describing internal components
* test.md - describes the testing methodology and details for how to tests

Other documents are referenced from with the above three

