from __future__ import annotations

"""Scene regression assertions: hearth_sleeper_north_edge_constraints

Human visual-check notes (OpenSCAD):
  - Boundary (Octagon) and NewHearth are similar to hearth_sleeper_constraints.
  - The key difference: the origin is defined using reference_edge='north' so that an offset
    is specified from the hearth front edge to the *north edge* of the sleeper.
  - What you’re checking visually: HearthSleeper's NORTH edge is exactly 2" south of y=0.
"""

from scene_tests.assertions._util import assert_almost_equal, assert_has_object, side_lengths


def assert_scene(resolved_scene: dict) -> None:
    hs = assert_has_object(resolved_scene, "HearthSleeper")
    fp = hs.get("geom", {}).get("footprint")
    if not (isinstance(fp, list) and len(fp) == 4):
        raise AssertionError("HearthSleeper expected footprint with 4 points")

    # Rationale: dim_lumber_member should resolve to a rectangle with correct physical dimensions.
    # Human reviewer expects: a 2x6 sleeper spanning the room width.
    lens = side_lengths(fp)
    assert_almost_equal(min(lens), 5.5, tol=1e-6, msg="HearthSleeper short side should be 5.5in")
    assert_almost_equal(max(lens), 167.0, tol=1e-6, msg="HearthSleeper long side should be 167in")

    ys = [float(p[1]) for p in fp]
    # Rationale: reference_edge='north' means the offset is measured to the north edge, not the
    # centerline.
    # Human reviewer expects: the sleeper is positioned so its north edge aligns at y=-2.
    assert_almost_equal(max(ys), -2.0, tol=1e-6, msg="HearthSleeper north edge should be at y=-2")
    assert_almost_equal(min(ys), -7.5, tol=1e-6, msg="HearthSleeper south edge should be at y=-7.5")

    # Rationale: Feature catalog for dim_lumber_member should include edges used by constraints.
    # Human reviewer expects: edge features exist (useful for downstream operators).
    edges = (hs.get("geom", {}).get("features", {}) or {}).get("edges", {})
    if "left" not in edges or "right" not in edges:
        raise AssertionError("Expected HearthSleeper geom.features.edges to include 'left' and 'right'")
