from __future__ import annotations

import argparse
import glob
import os
from pathlib import Path
import sys


def _default_outdir() -> str:
    # Use /tmp on Unix-y systems, fall back to cwd.
    return "/tmp/aicaddie_scene_tests" if os.path.isdir("/tmp") else os.path.abspath("./_scene_test_outputs")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate SCAD outputs for all scene regression cases (human-verified in OpenSCAD)."
    )
    parser.add_argument(
        "--cases",
        default=str(Path(__file__).parent / "cases"),
        help="Directory containing *.scene.json cases (default: scene_tests/cases)",
    )
    parser.add_argument(
        "--outdir",
        default=_default_outdir(),
        help="Directory to write generated .scad files (default: /tmp/aicaddie_scene_tests)",
    )
    parser.add_argument(
        "--pattern",
        default="*.scene.json",
        help="Glob pattern for case files (default: *.scene.json)",
    )
    args = parser.parse_args(argv)

    cases_dir = os.path.abspath(args.cases)
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    pattern = os.path.join(cases_dir, args.pattern)
    case_files = sorted(glob.glob(pattern))
    if not case_files:
        print(f"No scene cases found at: {pattern}")
        return 2

    # Import here to keep CLI snappy.
    from engine.run import run_file

    failures: list[tuple[str, str]] = []

    for path in case_files:
        base = os.path.basename(path)
        name = base
        for suf in (".scene.json", ".json"):
            if name.endswith(suf):
                name = name[: -len(suf)]
                break
        out_path = os.path.join(outdir, f"{name}.scad")
        try:
            run_file(path, out_path)
            print(f"OK   {base} -> {out_path}")
        except Exception as e:
            failures.append((base, str(e)))
            print(f"FAIL {base}: {e}")

    if failures:
        print("\nFailures:")
        for base, msg in failures:
            print(f"- {base}: {msg}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
