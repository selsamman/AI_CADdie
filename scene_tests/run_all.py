from __future__ import annotations

import argparse
import glob
import os
import shutil
import sys
import importlib
from pathlib import Path


def _repo_root() -> Path:
    # scene_tests/... -> repo root
    return Path(__file__).resolve().parent.parent


def _default_outdir() -> Path:
    return _repo_root() / "tmp" / "scene_tests_out"


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _maybe_run_scene_assertions(case_name: str, resolved_scene: dict) -> None:
    """If a per-scene assertion module exists, run it.

    Convention:
      scene_tests/assertions/<case_name>.py defines:
        def assert_scene(resolved_scene: dict) -> None
    """
    mod_name = f"scene_tests.assertions.{case_name}"
    try:
        mod = importlib.import_module(mod_name)
    except ModuleNotFoundError:
        return

    fn = getattr(mod, "assert_scene", None)
    if fn is None:
        raise AssertionError(f"{mod_name} exists but does not define assert_scene(resolved_scene)")
    fn(resolved_scene)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate SCAD outputs for scene regression cases and optionally compare against golden SCAD files."
        )
    )
    parser.add_argument(
        "--cases",
        default=str(Path(__file__).parent / "cases"),
        help="Directory containing *.scene.json cases (default: scene_tests/cases)",
    )
    parser.add_argument(
        "--golden",
        default=str(Path(__file__).parent / "golden"),
        help="Directory containing golden .scad files (default: scene_tests/golden)",
    )
    parser.add_argument(
        "--outdir",
        default=str(_default_outdir()),
        help="Directory to write generated .scad files (default: ./tmp/scene_tests_out)",
    )
    parser.add_argument(
        "--pattern",
        default="*.scene.json",
        help="Glob pattern for case files (default: *.scene.json)",
    )
    parser.add_argument(
        "--no-compare",
        action="store_true",
        help="Only generate outputs; do not compare against golden files.",
    )
    parser.add_argument(
        "--update-golden",
        action="store_true",
        help="Update golden files from generated outputs (overwrites scene_tests/golden/*.scad).",
    )
    args = parser.parse_args(argv)

    cases_dir = Path(os.path.abspath(args.cases))
    golden_dir = Path(os.path.abspath(args.golden))
    outdir = Path(os.path.abspath(args.outdir))
    outdir.mkdir(parents=True, exist_ok=True)
    golden_dir.mkdir(parents=True, exist_ok=True)

    pattern = str(cases_dir / args.pattern)
    case_files = sorted(glob.glob(pattern))
    if not case_files:
        print(f"No scene cases found at: {pattern}")
        return 2

    from engine.run import run_file_with_resolved

    failures: list[str] = []
    missing_golden: list[str] = []

    for path in case_files:
        base = os.path.basename(path)
        name = base
        for suf in (".scene.json", ".json"):
            if name.endswith(suf):
                name = name[: -len(suf)]
                break

        out_path = outdir / f"{name}.scad"
        out_scene_path = outdir / f"{name}.resolved.json"
        golden_path = golden_dir / f"{name}.scad"

        try:
            _scad_path, resolved = run_file_with_resolved(path, str(out_path), str(out_scene_path))
            _maybe_run_scene_assertions(name, resolved)
        except Exception as e:
            failures.append(f"[FAIL] {base}: {e}")
            continue

        if args.update_golden:
            shutil.copyfile(out_path, golden_path)
            print(f"[GOLDEN] {base} -> {golden_path}")
            continue

        if args.no_compare:
            print(f"[OK] {base} -> {out_path}")
            continue

        if not golden_path.exists():
            missing_golden.append(base)
            print(f"[MISSING GOLDEN] {base} (expected {golden_path})")
            continue

        got = _read_text(str(out_path))
        exp = _read_text(str(golden_path))
        if got != exp:
            failures.append(f"[DIFF] {base}: output does not match golden ({golden_path})")
            print(f"[FAIL] {base}")
        else:
            print(f"[PASS] {base}")

    if args.update_golden:
        return 0

    if missing_golden:
        print(
            "\nMissing golden files for:\n"
            + "\n".join(f"- {b}" for b in missing_golden)
            + "\n\nRun with --update-golden after verifying outputs in OpenSCAD."
        )
        # Treat missing goldens as failure unless user opted out of comparisons.
        return 1 if not args.no_compare else (1 if failures else 0)

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"- {f}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
