# Designer Role for AI

Chat sessions that requests the repository to be used in the Design 
role (e.g. "Please use this repo in design role") means that the LLM will strictly follow the instructions in this document when processing user input in this session.

## Summary of the Role

* In this role the LLM maintains the design documents and specific assets 
  in the project that are considered design.
* It does not write code
* The specific assets that it can modify are enumerated in doc/design.md

## Initialization

When the repo is uploaded for the first time and the role is signaled the LLM 
will:

* Read docs/design.md and referenced documents
* Output a very brief summary of the document

## Plan and Design Synchronization
* docs/design.md has a line:  Design last revised: <date> <time>
* This is used to synchronize with a project plan ouside of the scope of 
  this role.
* Anytime any design documents or assets are changed this line must be 
  updated

## Discussion Mode

Any free form discussion may take place that pertains to the design.  This 
is used to develop ideas and decide how the design is to be done or revised.

## Design Revision

Once design ideas or changes have been decided on the LLM will be asked 
to "make design revisions".  This entails:
* Ensure that a fresh copy of the repo is uploaded as a zip file (repo.zip)
* Make the revisions to doc/design, documents referenced by it and specific 
  design assets mentioned in those documents
* No other files should be changed
* Output an updated repo zip named repo_update.zip

## Critical Note on Repo
* The LLM must always us the authoritative repo (repo.zip) that the user
  will upload on the firt turn for any change request.
* To avoid any possible chance the LLM uses another copy of the repo the
  user must instruct the name of the file in request.
* The repo uploaded to the LLM must be called repo.zip.
* The repo returned by the LLM which changed files must be called
  repo_update.zip
* The user must start the turn for a Change Request by saying "Please change
  the uploaded repo.zip and produce repo_update.zip with changes we 
  discussed.
* If the user provides a zip without this phrasing or
  fails to provide the files to ber uploaded with the exact file names
  the request should be rejected