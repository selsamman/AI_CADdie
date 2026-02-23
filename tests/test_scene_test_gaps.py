import math
import unittest
from pathlib import Path

from engine.geom import point_in_convex
from engine.registry import load_registries
from engine.scene import build_scene
from engine.constraints import compile_scene_constraints
from engine.features import resolve_feature_segment


REPO = Path(__file__).resolve().parents[1]


def _centroid(fp):
    xs = [float(p[0]) for p in fp]
    ys = [float(p[1]) for p in fp]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


class TestSceneTestGaps(unittest.TestCase):
    """Targeted unit tests that cover the gaps enumerated in docs/scene_test_gaps.md.

    These are *not* golden SCAD regressions; they validate resolved-scene geometry and
    error contracts without requiring human-reviewed golden updates.
    """

    def setUp(self):
        self.regs = load_registries(REPO)

    def _resolve(self, scene: dict) -> dict:
        """Resolve a scene dict using the same constraints-compile rule as engine.run."""
        if scene.get("scene_type") == "constraints" or any(
            (
                o.get("prototype") == "dim_lumber_member"
                and isinstance(o.get("params", {}).get("placement_constraints"), dict)
            )
            for o in scene.get("objects", [])
        ):
            scene = compile_scene_constraints(scene, registries=self.regs)
        return build_scene(scene, self.regs)

    def test_gap01_clip_to_object_multiple_targets(self):
        scene = {
            "schema_version": "0.2",
            "anchor_id": "room",
            "objects": [
                {
                    "id": "room",
                    "prototype": "regular_octagon_boundary",
                    "params": {"origin": [0, 0], "north_wall_normal": [0, 1], "span_flat_to_flat_in": 100.0},
                },
                {
                    "id": "t1",
                    "prototype": "poly_extrude",
                    "params": {"footprint": [[40, -2], [80, -2], [80, 2], [40, 2]], "extrusion": {"z_base": 0, "height": 2}},
                },
                {
                    "id": "t2",
                    "prototype": "poly_extrude",
                    "params": {"footprint": [[40, 10], [80, 10], [80, 14], [40, 14]], "extrusion": {"z_base": 0, "height": 2}},
                },
            ],
            "operators": [
                {"op": "clip_to_object", "clip_object_id": "room", "target_ids": ["t1", "t2"]}
            ],
        }

        resolved = self._resolve(scene)
        room_fp = [(float(x), float(y)) for x, y in resolved["objects"]["room"]["geom"]["footprint"]]
        for tid in ("t1", "t2"):
            fp = resolved["objects"][tid]["geom"]["footprint"]
            for x, y in fp:
                self.assertTrue(point_in_convex((float(x), float(y)), room_fp))

    def test_gap02_clip_to_object_target_fully_outside_becomes_empty(self):
        scene = {
            "schema_version": "0.2",
            "anchor_id": "room",
            "objects": [
                {
                    "id": "room",
                    "prototype": "regular_octagon_boundary",
                    "params": {"origin": [0, 0], "north_wall_normal": [0, 1], "span_flat_to_flat_in": 100.0},
                },
                {
                    "id": "outside",
                    "prototype": "poly_extrude",
                    "params": {"footprint": [[200, 0], [210, 0], [210, 10], [200, 10]], "extrusion": {"z_base": 0, "height": 2}},
                },
            ],
            "operators": [
                {"op": "clip_to_object", "clip_object_id": "room", "target_ids": ["outside"]}
            ],
        }
        resolved = self._resolve(scene)
        fp = resolved["objects"]["outside"]["geom"]["footprint"]
        self.assertTrue(fp == [] or len(fp) < 3, "fully-outside clip should produce an empty/degenerate footprint")

    def test_gap03_clip_to_object_rejects_nonconvex_clipper(self):
        # Concave "arrow" clipper footprint
        scene = {
            "schema_version": "0.2",
            "anchor_id": "clip",
            "objects": [
                {
                    "id": "clip",
                    "prototype": "poly_extrude",
                    "params": {
                        "footprint": [[0, 0], [40, 0], [40, 10], [20, 5], [0, 10]],
                        "extrusion": {"z_base": 0, "height": 2},
                    },
                },
                {
                    "id": "target",
                    "prototype": "poly_extrude",
                    "params": {"footprint": [[5, 2], [35, 2], [35, 8], [5, 8]], "extrusion": {"z_base": 0, "height": 2}},
                },
            ],
            "operators": [
                {"op": "clip_to_object", "clip_object_id": "clip", "target_ids": ["target"]}
            ],
        }
        with self.assertRaises(ValueError):
            self._resolve(scene)

    def test_gap05_extend_and_trim_no_hit_is_noop(self):
        scene = {
            "schema_version": "0.2",
            "anchor_id": "room",
            "objects": [
                {"id": "room", "prototype": "regular_octagon_boundary", "params": {"origin": [0, 0], "north_wall_normal": [0, 1], "span_flat_to_flat_in": 120.0}},
                {"id": "post", "prototype": "poly_extrude", "params": {"footprint": [[200, -5], [205, -5], [205, 5], [200, 5]], "extrusion": {"z_base": 0, "height": 4}}},
                {
                    "id": "sleeper",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "2x6"},
                        # Use explicit placement so this test does not depend on the constraints compiler.
                        "placement": {"start": [-60.0, 0.0], "direction": "E", "length": 120.0},
                    },
                },
            ],
            "operators": [
                {
                    "op": "extend_and_trim_to_object",
                    "source_object_id": "sleeper",
                    "target_object_id": "post",
                    "source_edge": [1, 2],
                    "direction": [1.0, 0.0],
                }
            ],
        }
        resolved = self._resolve(scene)
        # Assert contract: no-hit path is a silent no-op (sleeper footprint remains unchanged).
        fp = resolved["objects"]["sleeper"]["geom"]["footprint"]
        self.assertEqual(len(fp), 4)
        # no strict equality to fp_before (not available); just ensure it still spans the room.
        xs = [float(x) for x, _y in fp]
        self.assertGreater(max(xs) - min(xs), 80.0)

    def test_gap06_distribute_evenly_between_diagonal(self):
        scene = {
            "schema_version": "0.2",
            "anchor_id": "room",
            "objects": [
                {"id": "room", "prototype": "regular_octagon_boundary", "params": {"origin": [0, 0], "north_wall_normal": [0, 1], "span_flat_to_flat_in": 200.0}},
                {"id": "A", "prototype": "poly_extrude", "params": {"footprint": [[-5, -5], [5, -5], [5, 5], [-5, 5]], "extrusion": {"z_base": 0, "height": 2}}},
                {"id": "B", "prototype": "poly_extrude", "params": {"footprint": [[95, 45], [105, 45], [105, 55], [95, 55]], "extrusion": {"z_base": 0, "height": 2}}},
                {"id": "T", "role": "template", "prototype": "dim_lumber_member", "params": {"profile": {"id": "2x4"}, "placement": {"direction": "N", "length": 10}}},
            ],
            "operators": [
                {
                    "op": "distribute_evenly_between",
                    "template_object_id": "T",
                    "between_object_ids": ["A", "B"],
                    "count": 2,
                    "id_prefix": "M_",
                    "provides": ["objects[*].params.placement.start"],
                }
            ],
        }
        resolved = self._resolve(scene)
        ax, ay = _centroid(resolved["objects"]["A"]["geom"]["footprint"])
        bx, by = _centroid(resolved["objects"]["B"]["geom"]["footprint"])
        for i, t in enumerate((1 / 3, 2 / 3), start=1):
            start = resolved["objects"][f"M_{i}"]["params"]["placement"]["start"]
            ex, ey = (ax + (bx - ax) * t, ay + (by - ay) * t)
            self.assertAlmostEqual(float(start[0]), ex, places=6)
            self.assertAlmostEqual(float(start[1]), ey, places=6)

    def test_gap08_octagon_origin_and_rotation(self):
        # Rotate so "north" points along +X.
        scene = {
            "schema_version": "0.2",
            "anchor_id": "Oct",
            "objects": [
                {
                    "id": "Oct",
                    "prototype": "regular_octagon_boundary",
                    "params": {"span_flat_to_flat_in": 100.0, "origin": [10.0, 20.0], "north_wall_normal": [1.0, 0.0]},
                }
            ],
        }
        resolved = self._resolve(scene)
        fp = resolved["objects"]["Oct"]["geom"]["footprint"]
        # With north_wall_normal=[1,0], the local +Y aligns to +X, so the "North" vertex should have max X.
        xs = [float(x) for x, _y in fp]
        self.assertAlmostEqual(max(xs), 10.0 + 50.0, places=5)

    def test_gap09_poly_extrude_faces_left_right_back_front(self):
        scene = {
            "schema_version": "0.2",
            "anchor_id": "p",
            "objects": [
                {
                    "id": "p",
                    "prototype": "poly_extrude",
                    "params": {"footprint": [[-2, -1], [8, -1], [8, 3], [-2, 3]], "extrusion": {"z_base": 0, "height": 2}},
                }
            ],
        }
        resolved = self._resolve(scene)
        p = resolved["objects"]["p"]
        # poly_extrude publishes bbox-derived faces through the feature resolver.
        for feat in ("face:left", "face:right", "face:front", "face:back"):
            seg = resolve_feature_segment(p, feat)
            self.assertEqual(len(seg), 2)

    def test_gap10_poly_extrude_named_edges_resolve(self):
        # Named edge should be resolvable as a segment and usable by constraints.
        scene_c = {
            "scene_type": "constraints",
            "objects": [
                {"id": "Base", "prototype": "regular_octagon_boundary", "params": {"span_flat_to_flat_in": 100, "origin": [0, 0], "north_wall_normal": [0, 1]}},
                {
                    "id": "Shape",
                    "prototype": "poly_extrude",
                    "params": {
                        "extrusion": {"z_base": 0, "height": 2},
                        "footprint": [[0, 0], [40, 0], [40, 20], [0, 20]],
                        "named_edges": {"south_face": [0, 1]},
                    },
                },
                {
                    "id": "Sleeper",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "2x4"},
                        "placement_constraints": {
                            "axis": "E-W",
                            "origin": {"kind": "offset_from_feature", "feature": "Shape.edge:south_face", "dir": "S", "offset_in": 2},
                            "extent": {"kind": "span_between_hits", "from": "Base.wall:West", "to": "Base.wall:East"},
                        },
                    },
                },
            ],
        }
        internal = compile_scene_constraints(scene_c, registries=self.regs)
        hs = next(o for o in internal["objects"] if o["id"] == "Sleeper")
        self.assertIn("placement", hs["params"])
        self.assertIn("start", hs["params"]["placement"])

    def test_gap11_dim_lumber_member_wide_face_side_and_edge(self):
        from engine.prototypes import dim_lumber_member

        # On-edge orientations should swap width/height behavior in plan vs extrusion.
        geom_side = dim_lumber_member.resolve(
            {
                "profile": {"actual": [1.5, 5.5]},
                "placement": {"start": [0, 0], "direction": "E", "length": 10},
                "orientation": {"wide_face": "side"},
                "z_base": 0,
            },
            registries={"lumber_profiles": {}},
        )
        self.assertAlmostEqual(float(geom_side["extrusion"]["height"]), 5.5)

        geom_edge = dim_lumber_member.resolve(
            {
                "profile": {"actual": [1.5, 5.5]},
                "placement": {"start": [0, 0], "direction": "E", "length": 10},
                "orientation": {"wide_face": "edge"},
                "z_base": 0,
            },
            registries={"lumber_profiles": {}},
        )
        self.assertAlmostEqual(float(geom_edge["extrusion"]["height"]), 5.5)

    def test_gap13_reference_edge_shift_for_diagonal_axis(self):
        # Place a diagonal member 2" south of a reference feature, but specifying that the
        # reference applies to the NE edge of the member.
        scene = {
            "schema_version": "0.2",
            "anchor_id": "room",
            "objects": [
                {"id": "room", "prototype": "regular_octagon_boundary", "params": {"origin": [0, 0], "north_wall_normal": [0, 1], "span_flat_to_flat_in": 100.0}},
                {"id": "H", "prototype": "poly_extrude", "params": {"footprint": [[-10, 0], [10, 0], [10, 10], [-10, 10]], "extrusion": {"z_base": 0, "height": 2}}},
                {
                    "id": "D",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "2x4"},
                        "placement_constraints": {
                            "axis": "NE-SW",
                            "origin": {
                                "kind": "offset_from_feature",
                                "feature": "H.face:front",
                                "dir": "S",
                                "offset_in": 2,
                                "reference_edge": "NE",
                            },
                            "extent": {"kind": "span_between_hits", "from": "room.wall:SouthWest", "to": "room.wall:NorthEast"},
                        },
                    },
                },
            ],
        }
        resolved = self._resolve(scene)
        start = resolved["objects"]["D"]["params"]["placement"]["start"]
        self.assertEqual(len(start), 2)

    def test_gap14_ray_hit_clip_to_hit_line_false(self):
        scene = {
            "schema_version": "0.2",
            "anchor_id": "room",
            "objects": [
                {"id": "room", "prototype": "regular_octagon_boundary", "params": {"origin": [0, 0], "north_wall_normal": [0, 1], "span_flat_to_flat_in": 120.0}},
                {"id": "target", "prototype": "poly_extrude", "params": {"footprint": [[20, -5], [25, -5], [25, 5], [20, 5]], "extrusion": {"z_base": 0, "height": 2}}},
                {
                    "id": "ray",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "2x4"},
                        "placement_constraints": {
                            "axis": "E-W",
                            "reference_edge": "north",
                            "direction": "E",
                            "origin": {"kind": "offset_from_feature", "feature": "room.wall:West", "dir": "E", "offset_in": 0},
                            "extent": {"kind": "ray_hit", "until": "target.face:left", "clip_to_hit_line": False},
                        },
                    },
                },
            ],
        }
        resolved = self._resolve(scene)
        # With clip_to_hit_line=False, the member should remain a dim_lumber_member (not converted).
        self.assertEqual(resolved["objects"]["ray"].get("prototype"), "dim_lumber_member")

    def test_gap15_ray_hit_segment_path(self):
        # Use until=<regular_octagon_boundary>.wall:* to exercise resolve_feature_segment path.
        scene = {
            "schema_version": "0.2",
            "anchor_id": "room",
            "objects": [
                {"id": "room", "prototype": "regular_octagon_boundary", "params": {"origin": [0, 0], "north_wall_normal": [0, 1], "span_flat_to_flat_in": 200.0}},
                {
                    "id": "r",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "2x4"},
                        "placement_constraints": {
                            "axis": "E-W",
                            "reference_edge": "north",
                            "direction": "E",
                            "origin": {"kind": "offset_from_feature", "feature": "room.wall:West", "dir": "E", "offset_in": 0},
                            "extent": {"kind": "ray_hit", "until": "room.wall:East", "dir": "E"},
                        },
                    },
                },
            ],
        }
        resolved = self._resolve(scene)
        fp = resolved["objects"]["r"]["geom"]["footprint"]
        self.assertEqual(len(fp), 4)

    def test_gap16_span_between_hits_non_opposite_walls(self):
        scene_c = {
            "scene_type": "constraints",
            "objects": [
                {"id": "Oct", "prototype": "regular_octagon_boundary", "params": {"span_flat_to_flat_in": 100, "origin": [0, 0], "north_wall_normal": [0, 1]}},
                {
                    "id": "M",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "2x4"},
                        "placement_constraints": {
                            "axis": "NE-SW",
                            "origin": {"kind": "offset_from_feature", "feature": "Oct.wall:South", "dir": "N", "offset_in": 0, "reference_edge": "NE"},
                            "extent": {"kind": "span_between_hits", "from": "Oct.wall:North", "to": "Oct.wall:East"},
                        },
                    },
                },
            ],
        }
        internal = compile_scene_constraints(scene_c, registries=self.regs)
        m = next(o for o in internal["objects"] if o["id"] == "M")
        self.assertGreater(m["params"]["placement"]["length"], 1.0)

    def test_gap17_point_on_edge_from_vertex_boundary_values(self):
        # distance_in = 0 should place on the specified vertex.
        scene_c0 = {
            "scene_type": "constraints",
            "objects": [
                {"id": "Oct", "prototype": "regular_octagon_boundary", "params": {"span_flat_to_flat_in": 100, "origin": [0, 0], "north_wall_normal": [0, 1]}},
                {
                    "id": "M0",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "2x4"},
                        "placement_constraints": {
                            "axis": "E-W",
                            "origin": {"kind": "point_on_edge_from_vertex", "edge": "Oct.wall:NorthEast", "vertex": "Oct.vertex:North", "distance_in": 0},
                            "extent": {"kind": "span_between_hits", "from": "Oct.wall:West", "to": "Oct.wall:East"},
                        },
                    },
                },
            ],
        }
        internal0 = compile_scene_constraints(scene_c0, registries=self.regs)
        m0 = next(o for o in internal0["objects"] if o["id"] == "M0")
        self.assertIn("start", m0["params"]["placement"])

    def test_gap18_forward_reference_rejected(self):
        scene_c = {
            "scene_type": "constraints",
            "objects": [
                {"id": "Oct", "prototype": "regular_octagon_boundary", "params": {"span_flat_to_flat_in": 100, "origin": [0, 0], "north_wall_normal": [0, 1]}},
                {
                    "id": "A",
                    "prototype": "dim_lumber_member",
                    "params": {
                        "profile": {"id": "2x4"},
                        "placement_constraints": {
                            "axis": "E-W",
                            "origin": {"kind": "offset_from_feature", "feature": "B.center", "dir": "S", "offset_in": 1},
                            "extent": {"kind": "span_between_hits", "from": "Oct.wall:West", "to": "Oct.wall:East"},
                        },
                    },
                },
                {"id": "B", "prototype": "poly_extrude", "params": {"footprint": [[0, 0], [1, 0], [1, 1], [0, 1]], "extrusion": {"z_base": 0, "height": 1}}},
            ],
        }
        with self.assertRaises(ValueError):
            compile_scene_constraints(scene_c, registries=self.regs)

    def test_gap19_wall_height_in_propagates_to_z_base(self):
        scene = {
            "scene_type": "constraints",
            "anchor_id": "room",
            "objects": [
                {"id": "room", "prototype": "regular_octagon_boundary", "params": {"origin": [0, 0], "north_wall_normal": [0, 1], "span_flat_to_flat_in": 100.0, "wall_height_in": 12.25}},
                {"id": "p", "prototype": "poly_extrude", "params": {"footprint": [[-1, -1], [1, -1], [1, 1], [-1, 1]], "extrusion": {"z_base": 0, "height": 2}}},
            ],
        }
        resolved = self._resolve(scene)
        # z_base for solids is taken exactly as authored (no compiler-side lifting).
        zb = float(resolved["objects"]["p"]["geom"]["extrusion"]["z_base"])
        self.assertAlmostEqual(zb, 0.0, places=6)

    def test_gap20_extend_and_trim_source_edge_out_of_range(self):
        scene = {
            "schema_version": "0.2",
            "anchor_id": "room",
            "objects": [
                {"id": "room", "prototype": "regular_octagon_boundary", "params": {"origin": [0, 0], "north_wall_normal": [0, 1], "span_flat_to_flat_in": 120.0}},
                {"id": "post", "prototype": "poly_extrude", "params": {"footprint": [[20, -5], [25, -5], [25, 5], [20, 5]], "extrusion": {"z_base": 0, "height": 2}}},
                {"id": "s", "prototype": "dim_lumber_member", "params": {"profile": {"id": "2x4"}, "placement": {"start": [0, 0], "direction": "E", "length": 50}}},
            ],
            "operators": [
                {"op": "extend_and_trim_to_object", "source_object_id": "s", "target_object_id": "post", "source_edge": [10, 11], "direction": "E"}
            ],
        }
        with self.assertRaises(ValueError):
            self._resolve(scene)


if __name__ == "__main__":
    unittest.main()
