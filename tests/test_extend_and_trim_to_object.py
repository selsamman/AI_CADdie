import json
import unittest
from pathlib import Path
from engine.scene import build_scene
from engine.registry import load_registries

REPO = Path(__file__).resolve().parents[1]

class TestExtendAndTrimToObject(unittest.TestCase):
    def test_sleeper_trims_to_post(self):
        registries = load_registries(REPO)
        scene = json.loads((REPO / "examples" / "extend_and_trim_minimal.scene.json").read_text(encoding="utf-8"))
        built = build_scene(scene, registries)

        sleeper = built["objects"]["sleeper"]["geom"]
        fp = sleeper["footprint"]
        xs = [p[0] for p in fp]

        # Post starts at x=39; after trim we expect sleeper max-x to be ~39 (within a small epsilon)
        self.assertLessEqual(max(xs), 39.0001)
        self.assertGreaterEqual(max(xs), 38.0)  # sanity: should not be wildly shorter

if __name__ == "__main__":
    unittest.main()
