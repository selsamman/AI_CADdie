#!/usr/bin/env python3
import json, sys
from pathlib import Path
from engine.registry import load_registries
from engine.scene import build_scene
from engine.scad import emit_scad

def main():
    if len(sys.argv) != 3:
        print("Usage: python engine/run.py scene.json out.scad")
        raise SystemExit(2)
    scene_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    registries = load_registries(Path(__file__).resolve().parents[1])
    resolved = build_scene(scene, registries)
    out_path.write_text(emit_scad(resolved), encoding="utf-8")
    print(f"Wrote {out_path}")

if __name__ == "__main__":
    main()
