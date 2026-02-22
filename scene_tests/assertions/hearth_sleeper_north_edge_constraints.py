from __future__ import annotations

from scene_tests.assertions._util import assert_almost_equal, assert_has_object, side_lengths


def assert_scene(resolved_scene: dict) -> None:
    hs = assert_has_object(resolved_scene, "HearthSleeper")
    fp = hs.get("geom", {}).get("footprint")
    if not (isinstance(fp, list) and len(fp) == 4):
        raise AssertionError("HearthSleeper expected footprint with 4 points")

    lens = side_lengths(fp)
    assert_almost_equal(min(lens), 5.5, tol=1e-6, msg="HearthSleeper short side should be 5.5in")
    assert_almost_equal(max(lens), 167.0, tol=1e-6, msg="HearthSleeper long side should be 167in")

    ys = [float(p[1]) for p in fp]
    # This case explicitly uses reference_edge='north'.
    assert_almost_equal(max(ys), -2.0, tol=1e-6, msg="HearthSleeper north edge should be at y=-2")
    assert_almost_equal(min(ys), -7.5, tol=1e-6, msg="HearthSleeper south edge should be at y=-7.5")
