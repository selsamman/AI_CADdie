# Testing for Development Process

Run all tests:

```bash
python -m unittest discover -s tests -v
```

This is run anytime the LLM changes any code in the repo.  Tests are added 
as needed to /tests.  Testing is not considered part of the design and it
is the responsiblity of the coder role to add additional tests that conform 
to Python's built-in unittest framework.

## Scene regression cases (human-verified)

In order to test constraints and the entire generationAs progresses,
we keep constraint scenes, generate scads for them and manually verify
that they are correct.  


```bash
python -m scene_tests.run_all
```
This creates the SCADs for all cases into `/tmp/aicaddie_scene_tests`:

Once they have been verified this is run to move them to scene_tests/golden

```bash
python -m scene_tests.run_all --update-golden
```

The regular unittest described above will now run the scene tests and 
compare them to golden.
