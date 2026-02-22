from __future__ import annotations

from scene_tests.assertions._util import assert_almost_equal, assert_has_object


def assert_scene(resolved_scene: dict) -> None:
    sleeper = assert_has_object(resolved_scene, "Sleeper")
    post = assert_has_object(resolved_scene, "Post")

    fp = sleeper["geom"]["footprint"]
    post_fp = post["geom"]["footprint"]

    # Post is an axis-aligned rectangle; its "left" face is min-x.
    post_min_x = min(float(x) for x, _y in post_fp)

    # extend_and_trim_to_object should trim Sleeper so its max-x matches the Post's left face.
    sleeper_max_x = max(float(x) for x, _y in fp)
    assert_almost_equal(sleeper_max_x, post_min_x, tol=1e-4)
