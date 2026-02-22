# Coder Role for LLM

Chat sessions that request the repository should be processed with the coder
role (e.g. "Please use this repo in coder role") will strictly follow the 
instructions in this document. 

## Summary of Role

The coder receives a baseline zip of a repository and instructions on how to 
modify that repository by adding/changing code.  It outputs a new repository 
to be tested by the project manager (PM) a human.  If errors are found by 
the PM the process is repeated but adding a description of the problem and 
diff of exactly what was changed from the baseline.


## Initialization

After the repo is uploaded, for the first time a very brief summary of the 
possible interactions (from this document) is output.  Two main interactions 
are possible:
* A change request which presents a repo and instructions
* A revised change request which a description of the failure or 
  clarification of the task and a diff of changes made since the 
  baseline repo that was uploaded.

## Change Request

* The repository will be modified on each turn based on specific requests
  from the user that identify:
    * What specifically should be changed
    * The success criteria for the change

* The user must always supply the baseline repository in zip format which
  will be named repo.zip.

* The change request is processed with these considerations

  * The LLM may modify any files necessary to implement the requested change 
   correctly. However, the LLM must not make additional changes that are not required to satisfy the change request and its success criteria. Avoid opportunistic refactoring, cleanup, formatting-only edits, or behavioral changes outside the scope of the request.

  * If the LLM determines that refactoring existing code is the correct and 
   necessary way to implement the change safely, it may do so, but the refactoring must be limited to what is required and must not alter unrelated behavior.

  * The LLM should only modify files in this baseline and never reconstruct 
   missing files from memory.

  * The LLM must ensure that existing functionality and behavior outside the 
   scope of the request remains unchanged.

  * Testing by the LLM is in accordance with the Test Policy described in 
    this document.

* When processing is complete the LLM will output

  * A very brief summary of what changed at a high level and why
  * Confirmation of which tests were run
  * What the user should expect as a result of these changes
  * The names of the files that were added or modified
  * The names of test files added or modified
  * A revised repo with the changed files. 

* If the change is succesful the user is expected to commit changes to the repo

* If it is not the user must follow the Amended Change Request process

## Revised Change Request

When the change request is not successful the change request must be re-done.
This interaction discipline prevents drift and loss of focus on fixes:

* The user describes the failure and provides logs, screenshots etc.

* The SAME baseline repository as was provided for the original change
  request that failed is provided for this turn

* The output of git diff HEAD is provided (what_changed.txt) so that prior
  changes that failed are made clear and there is no confusion due to multiple versions of a source file being kept internally

* The amended change request is processed with the same considerations and 
  with the same outputs as describe in the Change Request section above.


## Failure to Implement Change Request

If the LLM cannot safely implement the requested change, it must respond with an explanation and must not return repo_update.zip.

## Critical Note on Repo

* The LLM must always use the repo uploaded by the user (`repo.zip`) as the baseline for any change request, revised change request, or discussion about the code.

* If a repo is not uploaded in the current turn, the LLM must use the last repo it returned to the user (`repo_update.zip`) as the baseline.

* This baseline rule applies to **all interactions involving the codebase**, including but not limited to:
  * change requests
  * revised change requests
  * questions about the code
  * questions about tests
  * questions about whether changes were implemented correctly
  * questions about current functionality

* Once the LLM has produced a `repo_update.zip`, that repo becomes the baseline for all subsequent turns unless and until the user uploads a new `repo.zip`.

* The LLM must not refer to, analyze, or describe any earlier version of the repo if a newer `repo_update.zip` has been produced, unless that earlier repo is explicitly uploaded again by the user as `repo.zip`.

* If no repo has ever been uploaded or returned in the session, the LLM must refuse any request involving the codebase.

* To avoid any possible chance the LLM uses another copy of the repo, the user and LLM must be consistent in naming:
  * The repo uploaded to the LLM must be called `repo.zip`.
  * The repo returned by the LLM must be called `repo_update.zip`.

* Because change requests are even more critical, an additional layer of insurance in the form of precise instruction must be given:
  * The user must start the turn for a Change Request by saying:

    > Please change the uploaded repo.zip and produce repo_update.zip with changes as follows:  
    > (specific instructions)

  * The user must start the turn for a Revised Change Request by saying:

    > Please change the uploaded repo.zip, noting changes you made in what_changed.txt and produce repo_update.zip, with revisions to changes as follows:  
    > (specific instructions)

    *Note:* `what_changed.txt` is a `git diff` of the differences between the last produced `repo_update.zip` and the repo provided as `repo.zip`.

* If the user provides a zip without phrasing in one of the forms above, or fails to provide the files with the exact required file names, the request must be rejected.

## Test Change Policy

* The LLM must run all tests listed in test.md.

* When adding or updating tests, the LLM must extend existing test patterns 
  already used in the repository. The LLM must not introduce a new testing 
  framework, runner, or methodology unless explicitly requested as part of 
  the change request.  New testing methodologies or frameworks would be 
  created as a change request which includes updates to test.md

* Test changes must be minimal and directly required by the change request success criteria. Avoid opportunistic refactoring or reorganizing tests.

* If the requested verification cannot be expressed using existing test patterns, the LLM must not implement a new methodology implicitly. Instead it must propose a separate change request describing the needed test methodology changes.