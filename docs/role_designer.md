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

* The LLM must always use the repo uploaded by the user (`repo.zip`) as the baseline for any change request or discussion about the code.

* If a repo is not uploaded in the current turn, the LLM must use the last repo it returned to the user (`repo_update.zip`) as the baseline.

* This baseline rule applies to **all interactions involving the codebase**, including but not limited to:
  * change requests
  * questions about the code
  * questions about tests
  * questions about whether changes were implemented correctly
  * questions about current functionality
  * discussion of design changes

* Once the LLM has produced a `repo_update.zip`, that repo becomes the baseline for all subsequent turns unless and until the user uploads a new `repo.zip`.

* The LLM must not refer to, analyze, or describe any earlier version of the repo if a newer `repo_update.zip` has been produced, unless that earlier repo is explicitly uploaded again by the user as `repo.zip`.

* If no repo has ever been uploaded or returned in the session, the LLM must refuse any request involving the codebase.

* To avoid any possible chance the LLM uses another copy of the repo, the user and LLM must be consistent in naming:
  * The repo uploaded to the LLM must be called `repo.zip`.
  * The repo returned by the LLM must be called `repo_update.zip`.

* The user must start the turn for a Change Request by saying:

  > Please change the uploaded repo.zip and produce repo_update.zip with changes we discussed.

* If the user provides a zip without this phrasing, or fails to provide the files with the exact required file names, the request must be rejected.