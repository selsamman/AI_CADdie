from __future__ import annotations

"""Scene regression assertions: right_wing_sleeper_constraints

Human visual-check notes (OpenSCAD):
  - RightWingSleeper is a small diagonal (NE–SW axis) member originating 49" down the NE wall.
  - Its extent is ray_hit until it reaches the HearthSleeper footprint.
  - What you’re checking visually: the diagonal member should start on the NE wall and terminate
    exactly at the sleeper line (touching, with no visible gap).
"""

from scene_tests.assertions._util import assert_almost_equal, assert_has_object, side_lengths


def assert_scene(resolved_scene: dict) -> None:
    rws = assert_has_object(resolved_scene, "RightWingSleeper")
    fp = rws.get("geom", {}).get("footprint")
    if not (isinstance(fp, list) and len(fp) == 4):
        raise AssertionError("RightWingSleeper expected footprint with 4 points")

    # Rationale: The footprint dimensions should match the explicit actual profile.
    # Human reviewer expects: a thin sleeper strip (2.5" wide in plan).
    lens = side_lengths(fp)
    # Profile is explicitly 0.75" x 2.5". In footprint space the narrower side should be ~2.5".
    assert_almost_equal(min(lens), 2.5, tol=1e-6, msg="RightWingSleeper short side should be 2.5in")

    # Rationale: The ray_hit extent should terminate on the HearthSleeper footprint.
    # Human reviewer expects: RightWingSleeper meets the HearthSleeper at y≈-2 with no overrun.
    ys = [float(p[1]) for p in fp]
    assert_almost_equal(min(ys), -2.0, tol=1e-3, msg="RightWingSleeper should touch HearthSleeper at y≈-2")

    # Rationale: ray_hit with clip_to_hit_line=True is expected to emit a poly_extrude "cap" that
    # is clipped exactly at the hit line.
    # Human reviewer expects: the member end is flattened at the HearthSleeper contact.
    if rws.get("prototype") != "poly_extrude":
        raise AssertionError("Expected RightWingSleeper to be converted to poly_extrude by ray_hit clipping")
