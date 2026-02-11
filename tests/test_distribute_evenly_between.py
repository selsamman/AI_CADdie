import json
from pathlib import Path
import unittest

from engine.registry import load_registries
from engine.scene import build_scene

REPO = Path(__file__).resolve().parents[1]

class TestDistributeEvenlyBetween(unittest.TestCase):
    def test_distribute_generates_objects_from_template(self):
        registries = load_registries(REPO)

        scene = {
            "schema_version": "0.2",
            "anchor_id": "room",
            "objects": [
                {
                    "id": "room",
                    "prototype": "regular_octagon_boundary",
                    "params": {"origin":[0.0,0.0], "north_wall_normal":[0.0,1.0], "span_flat_to_flat_in": 100.0, "height_in": 10.0},
                    "style": {"color": [0.7,0.7,0.7,1.0]}
                },
                # Two concrete sleepers defining endpoints
                {
                    "id": "sleeper_a",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "S4S:5/4x2x3"},
                        "placement": {"start": [-20.0, -40.0], "direction": "east", "length": 60.0}
                    }
                },
                {
                    "id": "sleeper_b",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "S4S:5/4x2x3"},
                        "placement": {"start": [-20.0, 40.0], "direction": "east", "length": 60.0}
                    }
                },
                # Template sleeper (missing placement.start on purpose)
                {
                    "id": "sleeper_t",
                    "role": "template",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "S4S:5/4x2x3"},
                        "placement": {"direction": "east", "length": 60.0}
                    }
                }
            ],
            "operators": [
                {
                    "op": "distribute_evenly_between",
                    "template_object_id": "sleeper_t",
                    "between_object_ids": ["sleeper_a", "sleeper_b"],
                    "count": 2,
                    "id_prefix": "mid_",
                    "provides": ["objects[*].params.placement.start"]
                }
            ]
        }

        resolved = build_scene(scene, registries)
        self.assertIn("mid_1", resolved["objects"])
        self.assertIn("mid_2", resolved["objects"])
        self.assertNotIn("sleeper_t", resolved["objects"], "template objects should not be emitted")

        y1 = resolved["objects"]["mid_1"]["params"]["placement"]["start"][1]
        y2 = resolved["objects"]["mid_2"]["params"]["placement"]["start"][1]

        # Should be equally spaced between -40 and +40 (excluding endpoints): -13.333.. and +13.333..
        self.assertAlmostEqual(y1, -40.0 + (80.0/3.0), places=6)
        self.assertAlmostEqual(y2, -40.0 + (160.0/3.0), places=6)

if __name__ == "__main__":
    unittest.main()
