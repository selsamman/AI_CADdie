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


def run_file(scene_path: str | Path, out_path: str | Path) -> Path:
    """Run the pipeline for a single scene file and write a .scad output.

    This is used by regression runners (scene_tests) and by the CLI.
    """
    scene_path = Path(scene_path)
    out_path = Path(out_path)

    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    # If this is a constraints-authored scene, compile it to the internal scene schema.
    if scene.get("scene_type") == "constraints" or any(
        (
            o.get("prototype") == "dim_lumber_member"
            and isinstance(o.get("params", {}).get("placement_constraints"), dict)
        )
        for o in scene.get("objects", [])
    ):
        scene = compile_scene_constraints(scene)
    registries = load_registries(Path(__file__).resolve().parents[1])
    resolved = build_scene(scene, registries)
    out_path.write_text(emit_scad(resolved), encoding="utf-8")
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
