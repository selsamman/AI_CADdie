import json
import unittest
from pathlib import Path
from engine.scene import build_scene
from engine.registry import load_registries
from engine.geom import point_in_convex

REPO = Path(__file__).resolve().parents[1]

class TestClipToObject(unittest.TestCase):
    def test_block_clipped_inside_room(self):
        scene = json.loads((REPO / "examples" / "scene_example.json").read_text(encoding="utf-8"))
        regs = load_registries(REPO)
        resolved = build_scene(scene, regs)

        room_fp = resolved["objects"]["room"]["geom"]["footprint"]
        block_fp = resolved["objects"]["block"]["geom"]["footprint"]

        # Block footprint should exist (may gain extra vertices after clipping)
        self.assertTrue(len(block_fp) >= 3)

        # Every vertex must be inside/on the room boundary (convex)
        room_poly = [(float(x), float(y)) for x,y in room_fp]
        for x,y in block_fp:
            self.assertTrue(point_in_convex((float(x), float(y)), room_poly))

if __name__ == "__main__":
    unittest.main()
