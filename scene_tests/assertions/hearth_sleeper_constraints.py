from __future__ import annotations

"""Scene regression assertions: hearth_sleeper_constraints

Human visual-check notes (OpenSCAD):
  - Boundary (Octagon): You should see an 8-sided outline with flat-to-flat span 167".
    The flats should align N/S/E/W (i.e., it's "square-ish" in orientation, not rotated 22.5°).
  - NewHearth (poly_extrude): A 40"-wide rectangle (x=-20..20) that extrudes 10" tall,
    sitting just above the boundary visualization layer.
  - HearthSleeper (dim_lumber_member): A 2x6 sleeper spanning wall-to-wall (167" long),
    placed 2" south of the hearth front edge (y=0), with its north edge at y=-2.
"""

import math

from scene_tests.assertions._util import assert_almost_equal, assert_has_object, side_lengths


def _assert_regular_octagon_footprint(fp: list[list[float]], span_flat_to_flat_in: float) -> None:
    if not (isinstance(fp, list) and len(fp) == 8):
        raise AssertionError("Octagon expected footprint with 8 points")

    a = span_flat_to_flat_in / 2.0  # apothem
    b = a * math.tan(math.pi / 8.0)

    expected = [
        (-b, a),
        (b, a),
        (a, b),
        (a, -b),
        (b, -a),
        (-b, -a),
        (-a, -b),
        (-a, b),
    ]

    got = [(float(x), float(y)) for x, y in fp]

    # Sort by angle for stable matching.
    def ang(p: tuple[float, float]) -> float:
        return math.atan2(p[1], p[0])

    got_s = sorted(got, key=ang)
    exp_s = sorted(expected, key=ang)

    for (gx, gy), (ex, ey) in zip(got_s, exp_s):
        assert_almost_equal(gx, ex, tol=1e-5, msg=f"Octagon x mismatch: got {gx}, expected {ex}")
        assert_almost_equal(gy, ey, tol=1e-5, msg=f"Octagon y mismatch: got {gy}, expected {ey}")


def assert_scene(resolved_scene: dict) -> None:
    # Rationale: Baseline prototype sanity check for the canonical upright regular octagon.
    # Human reviewer expects: an upright (non-rotated) octagon boundary with correct proportions.
    octagon = assert_has_object(resolved_scene, "Octagon")
    oct_fp = octagon.get("geom", {}).get("footprint")
    _assert_regular_octagon_footprint(oct_fp, span_flat_to_flat_in=167.0)

    # Rationale: poly_extrude footprint + extrusion propagation.
    # Human reviewer expects: NewHearth is a 40" wide rectangle with front edge at y=0.
    hearth = assert_has_object(resolved_scene, "NewHearth")
    hearth_fp = hearth.get("geom", {}).get("footprint")
    if hearth_fp != [[-20, 20], [20, 20], [20, 0], [-20, 0]]:
        raise AssertionError("NewHearth footprint mismatch; expected 40x20 rectangle anchored at y=0")
    extr = hearth.get("geom", {}).get("extrusion")
    if not isinstance(extr, dict):
        raise AssertionError("NewHearth expected geom.extrusion dict")
    assert_almost_equal(float(extr.get("height")), 10.0, tol=1e-6, msg="NewHearth extrusion height should be 10")
    assert_almost_equal(float(extr.get("z_base")), 0.0, tol=1e-6, msg="NewHearth z_base should be 0.0")

    # Rationale: offset_from_feature + span_between_hits should place a sleeper wall-to-wall
    # with the requested reference edge alignment.
    # Human reviewer expects: HearthSleeper spans the full room width and sits 2" south of the hearth.
    hs = assert_has_object(resolved_scene, "HearthSleeper")
    fp = hs.get("geom", {}).get("footprint")
    if not (isinstance(fp, list) and len(fp) == 4):
        raise AssertionError("HearthSleeper expected footprint with 4 points")

    lens = side_lengths(fp)
    # 2x6 actual width is 5.5"; length spans the octagon flat-to-flat (167").
    assert_almost_equal(min(lens), 5.5, tol=1e-6, msg="HearthSleeper short side should be 5.5in")
    assert_almost_equal(max(lens), 167.0, tol=1e-6, msg="HearthSleeper long side should be 167in")

    ys = [float(p[1]) for p in fp]
    # This case is defined as 2" south of NewHearth.face:front (y=0), and uses the north edge as reference.
    assert_almost_equal(max(ys), -2.0, tol=1e-6, msg="HearthSleeper north edge should be at y=-2")
    assert_almost_equal(min(ys), -7.5, tol=1e-6, msg="HearthSleeper south edge should be at y=-7.5")
