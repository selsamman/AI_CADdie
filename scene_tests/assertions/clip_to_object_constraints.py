from __future__ import annotations

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
