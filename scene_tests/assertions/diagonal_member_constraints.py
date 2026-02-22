from __future__ import annotations

"""Scene regression assertions: diagonal_member_constraints

Human visual-check notes (OpenSCAD):
  - A single 2x6 member spans the room on a diagonal axis.
  - What you’re checking visually: the member appears diagonal (not axis-aligned), and spans
    approximately the room width.
"""

from scene_tests.assertions._util import assert_almost_equal, assert_has_object, side_lengths


def assert_scene(resolved_scene: dict) -> None:
    diag = assert_has_object(resolved_scene, "DiagonalSleeper")
    fp = diag.get("geom", {}).get("footprint")
    if not (isinstance(fp, list) and len(fp) == 4):
        raise AssertionError("DiagonalSleeper expected footprint with 4 points")

    # Rationale: A diagonal dim_lumber_member should still resolve to a rectangular footprint
    # with correct physical dimensions.
    # Human reviewer expects: width ~5.5" in plan and a long span across the room.
    lens = side_lengths(fp)
    # 2x6 footprint should be a rectangle: width 5.5", length spans octagon flat-to-flat: 167".
    assert_almost_equal(min(lens), 5.5, tol=1e-6, msg="DiagonalSleeper short side should be 5.5in")
    assert_almost_equal(max(lens), 167.0, tol=1e-6, msg="DiagonalSleeper long side should be 167in")
