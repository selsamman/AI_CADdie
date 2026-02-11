from __future__ import annotations
from typing import List, Tuple

Point = Tuple[float, float]
Poly = List[Point]

EPS = 1e-9

def signed_area(poly: Poly) -> float:
    if not poly:
        return 0.0
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1,y1 = poly[i]
        x2,y2 = poly[(i+1)%n]
        a += x1*y2 - y1*x2
    return 0.5*a

def is_ccw(poly: Poly) -> bool:
    return signed_area(poly) > 0

def _cross(ax: float, ay: float, bx: float, by: float) -> float:
    return ax*by - ay*bx

def _inside(p: Point, a: Point, b: Point, keep_left: bool) -> bool:
    ax, ay = a; bx, by = b; px, py = p
    cross = _cross(bx-ax, by-ay, px-ax, py-ay)
    return cross >= -EPS if keep_left else cross <= EPS

def _line_intersection(p1: Point, p2: Point, a: Point, b: Point) -> Point:
    # Intersection of lines (p1,p2) and (a,b); assumes they are not parallel.
    x1,y1 = p1; x2,y2 = p2
    x3,y3 = a;  x4,y4 = b
    den = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    if abs(den) < EPS:
        # Nearly parallel; return endpoint to keep algorithm stable.
        return p2
    px = ((x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)) / den
    py = ((x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)) / den
    return (px, py)

def clip_convex(subject: Poly, clipper: Poly) -> Poly:
    """Sutherland–Hodgman polygon clipping.

    - `clipper` must be convex.
    - Works for either winding direction of `clipper`.
    """
    if not subject or not clipper:
        return []
    keep_left = is_ccw(clipper)  # CCW => inside is left of each directed edge
    out = list(subject)
    m = len(clipper)
    for i in range(m):
        a = clipper[i]
        b = clipper[(i+1) % m]
        if not out:
            return []
        inp = out
        out = []
        prev = inp[-1]
        prev_in = _inside(prev, a, b, keep_left)
        for cur in inp:
            cur_in = _inside(cur, a, b, keep_left)
            if cur_in:
                if not prev_in:
                    out.append(_line_intersection(prev, cur, a, b))
                out.append(cur)
            else:
                if prev_in:
                    out.append(_line_intersection(prev, cur, a, b))
            prev, prev_in = cur, cur_in
    return out

def point_in_convex(p: Point, poly: Poly) -> bool:
    """Returns True if point is inside/on a convex polygon (either winding)."""
    if not poly:
        return False
    ccw = is_ccw(poly)
    n = len(poly)
    for i in range(n):
        a = poly[i]
        b = poly[(i+1)%n]
        if not _inside(p, a, b, keep_left=ccw):
            return False
    return True
