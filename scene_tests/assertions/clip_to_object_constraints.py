from __future__ import annotations

from scene_tests.assertions._util import assert_has_object
"""Scene regression assertions: clip_to_object_constraints

Human visual-check notes (OpenSCAD):
  - Boundary (Octagon): You should see the regular 8-sided outline with flat-to-flat span 167".
  - FarPost (poly_extrude): A small rectangular post far to the EAST (x ~ 195..205), clearly outside the Octagon.
    It’s there as a “tempting” out-of-bounds target for the sleeper’s unconstrained extent.
  - LongSleeper (dim_lumber_member): A long 2x4-ish member running E–W, originating from a point on the Octagon’s West wall.
    Before clipping, its extent tries to span toward the FarPost, so it *wants* to stick out of the Octagon on the east side.
  - What you’re checking visually: After clip_to_object, the LongSleeper geometry should NOT protrude outside the Octagon.
    The sleeper should appear truncated exactly at the Octagon boundary; no vertices / edges should be visible beyond the Octagon outline.
"""

def _is_inside_convex(poly: list[list[float]], pt: tuple[float, float], *, tol: float = 1e-6) -> bool:
    """Return True if pt lies inside-or-on a convex polygon (CCW or CW)."""
    x, y = pt
    pts = [(float(px), float(py)) for px, py in poly]
    if len(pts) < 3:
        return False

    sign = 0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        # cross((edge), (pt - v1))
        cx = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if abs(cx) <= tol:
            continue
        s = 1 if cx > 0 else -1
        if sign == 0:
            sign = s
        elif s != sign:
            return False
    return True


def assert_scene(resolved_scene: dict) -> None:
    octo = assert_has_object(resolved_scene, "Octagon")
    sleeper = assert_has_object(resolved_scene, "LongSleeper")
    octo_fp = octo["geom"]["footprint"]
    fp = sleeper["geom"]["footprint"]

    # clip_to_object should ensure all vertices lie within the Octagon boundary.
    for x, y in fp:
        if not _is_inside_convex(octo_fp, (float(x), float(y))):
            raise AssertionError(
                f"Expected LongSleeper vertex ({x},{y}) to be inside Octagon after clipping"
            )
