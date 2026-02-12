import unittest
from engine.constraints import compile_scene_constraints

class TestConstraintsCompiler(unittest.TestCase):
    def test_hearth_sleeper_offset_and_span(self):
        scene_c = {
            "scene_type": "constraints",
            "objects": [
                {
                    "id": "Octagon",
                    "prototype": "regular_octagon_boundary",
                    "params": {
                        "span_flat_to_flat_in": 167,
                        "origin": [0,0],
                        "north_wall_normal": [0,1]
                    }
                },
                {
                    "id": "NewHearth",
                    "prototype": "poly_extrude",
                    "params": {
                        "extrusion": {"z_base": 0, "height": 10},
                        "footprint": [[-20, 20], [20,20], [20,0], [-20,0]]
                    }
                },
                {
                    "id": "HearthSleeper",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "2x6"},
                        "placement_constraints": {
                            "axis": "E-W",
                            "origin": {
                                "kind": "offset_from_feature",
                                "feature": "NewHearth.face:front",
                                "dir": "S",
                                "offset_in": 2
                            },
                            "extent": {
                                "kind": "span_between_hits",
                                "from": "Octagon.wall:West",
                                "to": "Octagon.wall:East"
                            }
                        }
                    }
                }
            ]
        }
        internal = compile_scene_constraints(scene_c)
        # HearthSleeper now has numeric placement
        hs = next(o for o in internal["objects"] if o["id"] == "HearthSleeper")
        placement = hs["params"]["placement"]
        self.assertIn("start", placement)
        self.assertIn("direction", placement)
        self.assertIn("length", placement)
        # Direction should be eastward for an E-W span
        self.assertIn(str(placement["direction"]).lower(), ("e", "east"))
        # Length should be roughly the octagon span (a bit less due to chamfers)
        self.assertGreater(placement["length"], 140.0)
        self.assertLess(placement["length"], 200.0)

if __name__ == "__main__":
    unittest.main()
