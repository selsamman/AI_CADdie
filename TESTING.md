# Testing

Run all tests:

```bash
python -m unittest discover -s tests -v
```

The smoke test runs the example scene through `engine/build.py` and asserts an `out.scad` is produced.
