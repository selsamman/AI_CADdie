import unittest
from pathlib import Path

from engine.scene import build_scene
from engine.registry import load_registries

REPO = Path(__file__).resolve().parents[1]


class TestExtendAndTrimToObject(unittest.TestCase):
    def test_trims_block_to_target_first_touch(self):
        regs = load_registries(REPO)

        scene = {
            "schema_version": "0.2",
            "anchor_id": "src",
            "objects": [
                {
                    "id": "src",
                    "prototype": "poly_extrude",
                    "params": {
                        "footprint": [[0, 0], [10, 0], [10, 2], [0, 2]],
                        "extrusion": {"z_base": 0, "height": 1}
                    }
                },
                {
                    "id": "tgt",
                    "prototype": "poly_extrude",
                    "params": {
                        "footprint": [[6, -5], [8, -5], [8, 5], [6, 5]],
                        "extrusion": {"z_base": 0, "height": 4}
                    }
                }
            ],
            "operators": [
                {
                    "op": "extend_and_trim_to_object",
                    "source_object_id": "src",
                    "source_edge": [0, 3],
                    "direction": [1, 0],
                    "target_object_id": "tgt"
                }
            ]
        }

        resolved = build_scene(scene, regs)
        fp = resolved["objects"]["src"]["geom"]["footprint"]

        xs = [float(p[0]) for p in fp]
        self.assertAlmostEqual(min(xs), 0.0, places=6)
        # should be trimmed to the target's left face at x=6
        self.assertAlmostEqual(max(xs), 6.0, places=6)


if __name__ == "__main__":
    unittest.main()
