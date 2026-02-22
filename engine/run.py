#!/usr/bin/env python3
import json, sys
from pathlib import Path

# Allow running as `python engine/run.py` as well as `python -m engine.run`
if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.registry import load_registries
from engine.scene import build_scene
from engine.constraints import compile_scene_constraints
from engine.scad import emit_scad


def _load_and_resolve_scene(scene_path: Path, registries: dict) -> dict:
    """Load a scene file, compile constraints (if applicable), and build the resolved scene."""
    scene = json.loads(scene_path.read_text(encoding="utf-8"))

    # If constraints-authored, compile to internal schema (registries allow resolving lumber dims during compile).
    if scene.get("scene_type") == "constraints" or any(
        (
            o.get("prototype") == "dim_lumber_member"
            and isinstance(o.get("params", {}).get("placement_constraints"), dict)
        )
        for o in scene.get("objects", [])
    ):
        scene = compile_scene_constraints(scene, registries=registries)

    return build_scene(scene, registries)


def run_file_with_resolved(
    scene_path: str | Path,
    out_path: str | Path,
    out_scene_json_path: str | Path | None = None,
) -> tuple[Path, dict]:
    """Run the pipeline for a single scene file and write artifacts.

    Writes:
      - SCAD output to out_path
      - (optional) resolved scene JSON to out_scene_json_path

    Returns:
      (out_path, resolved_scene_dict)
    """
    scene_path = Path(scene_path)
    out_path = Path(out_path)
    out_scene_json_path = Path(out_scene_json_path) if out_scene_json_path else None

    registries = load_registries(Path(__file__).resolve().parents[1])
    resolved = _load_and_resolve_scene(scene_path, registries)

    out_path.write_text(emit_scad(resolved), encoding="utf-8")
    if out_scene_json_path is not None:
        out_scene_json_path.parent.mkdir(parents=True, exist_ok=True)
        out_scene_json_path.write_text(
            json.dumps(resolved, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return out_path, resolved


def run_file(scene_path: str | Path, out_path: str | Path) -> Path:
    """Run the pipeline for a single scene file and write a .scad output."""
    out_path, _resolved = run_file_with_resolved(scene_path, out_path, out_scene_json_path=None)
    return out_path


def main():
    if len(sys.argv) != 3:
        print("Usage: python -m engine.run scene.json out.scad")
        raise SystemExit(2)
    scene_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    run_file(scene_path, out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
