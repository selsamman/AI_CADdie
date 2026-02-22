from __future__ import annotations

from scene_tests.assertions._util import assert_almost_equal, assert_has_object, side_lengths


def assert_scene(resolved_scene: dict) -> None:
    rws = assert_has_object(resolved_scene, "RightWingSleeper")
    fp = rws.get("geom", {}).get("footprint")
    if not (isinstance(fp, list) and len(fp) == 4):
        raise AssertionError("RightWingSleeper expected footprint with 4 points")

    lens = side_lengths(fp)
    # Profile is explicitly 0.75" x 2.5". In footprint space the narrower side should be ~2.5".
    assert_almost_equal(min(lens), 2.5, tol=1e-6, msg="RightWingSleeper short side should be 2.5in")

    # Extent is a ray_hit that terminates on the HearthSleeper footprint.
    # In this case the HearthSleeper north edge is at y=-2, so the wing sleeper should touch y=-2.
    ys = [float(p[1]) for p in fp]
    assert_almost_equal(min(ys), -2.0, tol=1e-3, msg="RightWingSleeper should touch HearthSleeper at y≈-2")
