from __future__ import annotations

"""Scene regression assertions: clip_to_object_constraints

Human visual-check notes (OpenSCAD):
  - Boundary (Octagon): regular 8-sided outline with flat-to-flat span 167".
  - FarPost (poly_extrude): small rectangle far to the EAST (x ~ 195..205), outside the Octagon.
  - LongSleeper (dim_lumber_member): long E–W member that *wants* to extend toward FarPost.
  - What you’re checking visually: After clip_to_object, LongSleeper should be truncated at
    the Octagon boundary. No edges or vertices should protrude beyond the Octagon outline.
"""

from scene_tests.assertions._util import assert_has_object


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

    # Rationale: This case exists to ensure clip_to_object enforces plan-footprint clipping
    # against a convex room boundary.
    # Human reviewer expects: LongSleeper ends flush at the Octagon boundary on the east side.
    for x, y in fp:
        if not _is_inside_convex(octo_fp, (float(x), float(y))):
            raise AssertionError(
                f"Expected LongSleeper vertex ({x},{y}) to be inside Octagon after clipping"
            )

    # Rationale: A clipped footprint should remain a valid polygon (or empty in degenerate
    # cases). For this scene, we expect it to remain non-empty.
    # Human reviewer expects: a visible sleeper body (not dropped).
    if len(fp) < 3:
        raise AssertionError("Expected LongSleeper footprint to remain non-empty after clipping")
