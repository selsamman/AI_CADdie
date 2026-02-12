import unittest
from engine.prototypes import dim_lumber_member

class TestDimLumberMember(unittest.TestCase):
    def test_profile_actual_down(self):
        geom = dim_lumber_member.resolve({
            "profile": {"actual": [1.0, 2.5]},
            "placement": {"start":[0,0], "direction":"east", "length":10},
            "orientation": {"wide_face":"down"},
            "z_base": 0
        }, registries={"lumber_profiles":{}})

        self.assertEqual(geom["kind"], "solid")
        self.assertAlmostEqual(geom["extrusion"]["height"], 1.0)
        fp = geom["footprint"]
        # Expect rectangle from x=0..10, y=-1.25..1.25 (order CCW)
        xs = [p[0] for p in fp]; ys = [p[1] for p in fp]
        self.assertAlmostEqual(min(xs), 0.0)
        self.assertAlmostEqual(max(xs), 10.0)
        self.assertAlmostEqual(min(ys), -1.25)
        self.assertAlmostEqual(max(ys), 1.25)

    def test_profile_registry_nominal(self):
        regs = {"lumber_profiles": {"S4S:5/4x2x3": {"actual":[1.0, 2.5]}}}
        geom = dim_lumber_member.resolve({
            "profile": {"system":"S4S", "nominal":"5/4x2x3"},
            "placement": {"start":[1,2], "direction":"north", "length":8},
        }, registries=regs)
        fp = geom["footprint"]
        xs = [p[0] for p in fp]; ys=[p[1] for p in fp]
        self.assertAlmostEqual(min(ys), 2.0)     # start end centered at y=2, going north
        self.assertAlmostEqual(max(ys), 10.0)    # 2+8
        self.assertAlmostEqual(min(xs), 1.0-1.25)
        self.assertAlmostEqual(max(xs), 1.0+1.25)

    def test_unknown_profile_fails(self):
        with self.assertRaises(ValueError):
            dim_lumber_member.resolve({
                "profile": {"id":"S4S:DOES_NOT_EXIST"},
                "placement": {"start":[0,0], "direction":"east", "length":10},
            }, registries={"lumber_profiles":{}})

    def test_reference_edge_north(self):
        """If placement.start is given on the north edge, reference_edge='north' should shift to centerline."""
        geom = dim_lumber_member.resolve({
            "profile": {"actual": [1.0, 2.5]},
            # For an east-running board, the north edge is at y=+1.25 relative to centerline.
            "placement": {"start": [0, 1.25], "direction": "east", "length": 10, "reference_edge": "north"},
            "orientation": {"wide_face": "down"},
            "z_base": 0
        }, registries={"lumber_profiles": {}})
        fp = geom["footprint"]
        ys = [p[1] for p in fp]
        # After adjusting, centerline should be y=0, so edges should be at +/-1.25
        self.assertAlmostEqual(min(ys), -1.25)
        self.assertAlmostEqual(max(ys), 1.25)

if __name__ == "__main__":
    unittest.main()
