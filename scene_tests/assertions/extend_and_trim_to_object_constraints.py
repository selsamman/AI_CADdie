from __future__ import annotations

from scene_tests.assertions._util import assert_almost_equal, assert_has_object

"""Scene regression assertions: extend_and_trim_to_object_constraints

Human visual-check notes (OpenSCAD):
  - Boundary (Octagon): Regular 8-sided outline (167" flat-to-flat) as the anchor.
  - Post (poly_extrude): A thin vertical rectangle near x ~ 60..62 (y ~ -10..10). This is the TRIM target.
    Its “left face” is at x ~ 60.
  - FarPost (poly_extrude): Another rectangle far to the EAST (x ~ 195..205), used only to ensure the Sleeper is
    initially long enough (i.e., its raw span tries to go well past the Post).
  - Sleeper (dim_lumber_member): An E–W member starting on the Octagon’s West wall.
    Its initial extent is long (it spans toward FarPost), but extend_and_trim_to_object should trim it.
  - What you’re checking visually: The Sleeper’s EAST end should terminate exactly on the Post’s left face (x ~ 60),
    even though the FarPost is much farther east. In other words, the sleeper should stop at the Post, not at/near FarPost.
"""
def assert_scene(resolved_scene: dict) -> None:
    sleeper = assert_has_object(resolved_scene, "Sleeper")
    post = assert_has_object(resolved_scene, "Post")

    fp = sleeper["geom"]["footprint"]
    post_fp = post["geom"]["footprint"]

    # Rationale: The Post is the trim target; its left face defines the expected termination plane.
    # Human reviewer expects: Sleeper ends exactly on the Post's left face (flush abutment).
    post_min_x = min(float(x) for x, _y in post_fp)

    # Rationale: extend_and_trim_to_object (current v0.2) trims only; it should shorten the
    # sleeper so the far end aligns to the target face.
    # Human reviewer expects: Sleeper stops at Post, not at FarPost.
    sleeper_max_x = max(float(x) for x, _y in fp)
    assert_almost_equal(sleeper_max_x, post_min_x, tol=1e-4)

    # Rationale: trimming should not move the sleeper's origin side on the west wall.
    # Human reviewer expects: west end stays at the wall; only the east end is shortened.
    sleeper_min_x = min(float(x) for x, _y in fp)
    if sleeper_min_x > -80.0:
        raise AssertionError("Expected Sleeper west end to remain near the Octagon west wall")
