from __future__ import annotations

import argparse
import difflib
import glob
import os
from pathlib import Path
import sys


def _default_outdir() -> str:
    # Prefer a repo-local tmp dir so results are easy to inspect and can be ignored in git.
    return os.path.abspath("./tmp/scene_tests_out")


def _default_golden_dir() -> str:
    return str(Path(__file__).parent / "golden")


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _unified_diff(a_text: str, b_text: str, a_name: str, b_name: str, max_lines: int = 200) -> str:
    a_lines = a_text.splitlines(keepends=True)
    b_lines = b_text.splitlines(keepends=True)
    diff = difflib.unified_diff(a_lines, b_lines, fromfile=a_name, tofile=b_name)
    out: list[str] = []
    for i, line in enumerate(diff):
        if i >= max_lines:
            out.append(f"... (diff truncated at {max_lines} lines)\n")
            break
        out.append(line)
    return "".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run scene regression cases. Generates SCAD for each case and compares against golden outputs. "
            "Use --update-golden to bless new outputs."
        )
    )
    parser.add_argument(
        "--cases",
        default=str(Path(__file__).parent / "cases"),
        help="Directory containing *.scene.json cases (default: scene_tests/cases)",
    )
    parser.add_argument(
        "--outdir",
        default=_default_outdir(),
        help="Directory to write generated .scad files (default: ./tmp/scene_tests_out)",
    )
    parser.add_argument(
        "--pattern",
        default="*.scene.json",
        help="Glob pattern for case files (default: *.scene.json)",
    )

    parser.add_argument(
        "--golden-dir",
        default=_default_golden_dir(),
        help="Directory containing golden .scad files (default: scene_tests/golden)",
    )

    parser.add_argument(
        "--update-golden",
        action="store_true",
        help="Overwrite golden .scad files with newly generated outputs.",
    )

    parser.add_argument(
        "--no-compare",
        action="store_true",
        help="Only generate outputs; do not compare against golden files.",
    )
    args = parser.parse_args(argv)

    cases_dir = os.path.abspath(args.cases)
    outdir = os.path.abspath(args.outdir)
    golden_dir = os.path.abspath(args.golden_dir)
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(golden_dir, exist_ok=True)

    pattern = os.path.join(cases_dir, args.pattern)
    case_files = sorted(glob.glob(pattern))
    if not case_files:
        print(f"No scene cases found at: {pattern}")
        return 2

    # Import here to keep CLI snappy.
    from engine.run import run_file

    failures: list[tuple[str, str]] = []
    missing_golden: list[str] = []

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
            if args.no_compare:
                print(f"OK   {base} -> {out_path}")
                continue

            golden_path = os.path.join(golden_dir, f"{name}.scad")

            generated = _read_text(out_path)
            if args.update_golden:
                _write_text(golden_path, generated)
                print(f"BLESSED {base} -> {golden_path}")
                continue

            if not os.path.exists(golden_path):
                missing_golden.append(f"{name}.scad")
                print(f"MISSING_GOLDEN {base}: expected {golden_path}")
                continue

            expected = _read_text(golden_path)
            if generated == expected:
                print(f"PASS {base}")
            else:
                diff = _unified_diff(expected, generated, f"golden/{name}.scad", f"out/{name}.scad")
                failures.append((base, diff or "SCAD differs"))
                print(f"FAIL {base}: output differs from golden")
        except Exception as e:
            failures.append((base, str(e)))
            print(f"FAIL {base}: {e}")

    if missing_golden and not args.no_compare and not args.update_golden:
        print("\nMissing golden files:")
        for f in missing_golden:
            print(f"- {f}")
        print("\nTo create/update goldens, re-run with: --update-golden")
        return 3

    if failures:
        print("\nFailures:")
        for base, msg in failures:
            print(f"\n--- {base} ---")
            print(msg)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
