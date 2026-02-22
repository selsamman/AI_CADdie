from __future__ import annotations

from scene_tests.assertions._util import assert_almost_equal, assert_has_object

"""Scene regression assertions: distribute_evenly_between_constraints

Human visual-check notes (OpenSCAD):
  - A and B (poly_extrude): Two small square markers centered near x ~ 0 and x ~ 100 (both around y ~ 0).
    These define the endpoints for distribution (centroid-to-centroid).
  - StudTemplate (dim_lumber_member, role=template): Not necessarily rendered as a final object; it defines the
    member shape/orientation (2x4, “north” direction, length ~ 10).
  - Generated studs: You should see THREE studs: Stud_1, Stud_2, Stud_3.
  - What you’re checking visually: The studs should be placed evenly along the straight line from A’s centroid to B’s centroid:
      * Stud_1 at ~25% (x ~ 25)
      * Stud_2 at ~50% (x ~ 50)
      * Stud_3 at ~75% (x ~ 75)
    They should share the template’s orientation (pointing “north”) and appear evenly spaced between A and B.
"""

def _centroid(fp: list[list[float]]) -> tuple[float, float]:
    xs = [float(p[0]) for p in fp]
    ys = [float(p[1]) for p in fp]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def assert_scene(resolved_scene: dict) -> None:
    a = assert_has_object(resolved_scene, "A")
    b = assert_has_object(resolved_scene, "B")

    ax, ay = _centroid(a["geom"]["footprint"])
    bx, by = _centroid(b["geom"]["footprint"])

    # Rationale: distribute_evenly_between should place copies at evenly spaced interpolation
    # parameters between the anchor centroids.
    # Human reviewer expects: 3 studs evenly spaced between A and B, with matching orientation.
    for i, t in enumerate((0.25, 0.5, 0.75), start=1):
        sid = f"Stud_{i}"
        stud = assert_has_object(resolved_scene, sid)
        start = (stud.get("params", {}) or {}).get("placement", {}).get("start")
        if not (isinstance(start, list) and len(start) == 2):
            raise AssertionError(f"Expected {sid}.params.placement.start to exist")
        sx, sy = float(start[0]), float(start[1])

        ex = ax + (bx - ax) * t
        ey = ay + (by - ay) * t

        # Rationale: placement.start is the canonical "anchor point" for the member centerline.
        # Human reviewer expects: Stud_{i} appears centered at the expected interpolated point.
        assert_almost_equal(sx, ex, tol=1e-6, msg=f"{sid} start.x should be interpolated")
        assert_almost_equal(sy, ey, tol=1e-6, msg=f"{sid} start.y should be interpolated")

        # Rationale: Generated objects must have concrete geometry emitted.
        # Human reviewer expects: each Stud_{i} is visible as a small rectangular member.
        fp = stud.get("geom", {}).get("footprint")
        if not (isinstance(fp, list) and len(fp) == 4):
            raise AssertionError(f"Expected {sid} to have a 4-point rectangular footprint")
