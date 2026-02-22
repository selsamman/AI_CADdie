from __future__ import annotations

"""Scene regression assertions: rect_solid_constraints

This case exists to validate the rect_solid prototype's footprint geometry and
feature-handle wiring (engine/features.py).

Scene:
  - Octagon: 167" flat-to-flat, origin [0,0], north_wall_normal [0,1]
  - Chimney: rect_solid, 52" wide, 47" deep, 120" tall, back against North wall
"""

import math

from engine.features import resolve_feature_point, resolve_feature_segment
from scene_tests.assertions._util import assert_almost_equal, assert_has_object


def _dist(a: list[float], b: list[float]) -> float:
    return math.hypot(float(b[0]) - float(a[0]), float(b[1]) - float(a[1]))


def assert_scene(resolved_scene: dict) -> None:
    chim = assert_has_object(resolved_scene, "Chimney")

    fp = chim["geom"]["footprint"]

    # The footprint has exactly 4 points.
    if len(fp) != 4:
        raise AssertionError(f"Expected Chimney footprint to have 4 points, got {len(fp)}")

    # Footprint width: distance between back-left and back-right is 52".
    assert_almost_equal(_dist(fp[0], fp[1]), 52.0, tol=1e-4)

    # Footprint depth: distance between back-left and front-left is 47".
    assert_almost_equal(_dist(fp[0], fp[3]), 47.0, tol=1e-4)

    # corner:back_left resolves to approximately (-26, 83.5).
    blx, bly = resolve_feature_point(chim, "corner:back_left")
    assert_almost_equal(float(blx), -26.0, tol=1e-4)
    assert_almost_equal(float(bly), 83.5, tol=1e-4)

    # corner:front_right resolves to approximately (26, 36.5).
    frx, fry = resolve_feature_point(chim, "corner:front_right")
    assert_almost_equal(float(frx), 26.0, tol=1e-4)
    assert_almost_equal(float(fry), 36.5, tol=1e-4)

    # face:front resolves to the segment between front-left and front-right, both at y ≈ 36.5.
    (ax, ay), (bx, by) = resolve_feature_segment(chim, "face:front")
    assert_almost_equal(float(ay), 36.5, tol=1e-4)
    assert_almost_equal(float(by), 36.5, tol=1e-4)
