from __future__ import annotations
from typing import List, Tuple

Point = Tuple[float, float]
Poly = List[Point]

EPS = 1e-9

def dot(ax: float, ay: float, bx: float, by: float) -> float:
    return ax*bx + ay*by

def clip_halfplane(subject: Poly, p0: Point, n: Point, keep_leq: bool = True) -> Poly:
    """Clip a (possibly non-convex) polygon against a half-plane.

    Half-plane is defined by: dot((p - p0), n) <= 0 if keep_leq else >= 0.
    Uses a Sutherland–Hodgman-style pass over subject edges.
    """
    if not subject:
        return []
    nx, ny = n
    x0, y0 = p0

    def inside(p: Point) -> bool:
        px, py = p
        v = dot(px - x0, py - y0, nx, ny)
        return v <= EPS if keep_leq else v >= -EPS

    def intersect(a: Point, b: Point) -> Point:
        ax, ay = a
        bx, by = b
        dax, day = bx-ax, by-ay
        denom = dot(dax, day, nx, ny)
        if abs(denom) < EPS:
            return b
        t = -dot(ax - x0, ay - y0, nx, ny) / denom
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        return (ax + t*dax, ay + t*day)

    out: Poly = []
    prev = subject[-1]
    prev_in = inside(prev)
    for cur in subject:
        cur_in = inside(cur)
        if cur_in:
            if not prev_in:
                out.append(intersect(prev, cur))
            out.append(cur)
        else:
            if prev_in:
                out.append(intersect(prev, cur))
        prev, prev_in = cur, cur_in
    return out

def ray_segment_intersection(ro: Point, rd: Point, a: Point, b: Point) -> Tuple[bool, float, Point]:
    """Intersect ray (ro + t*rd, t>=0) with segment a->b.

    Returns (hit, t_ray, point). If no hit, hit=False.
    """
    rdx, rdy = rd
    ax, ay = a
    bx, by = b
    sx, sy = bx-ax, by-ay

    # Solve ro + t*rd = a + u*(b-a)
    den = _cross(rdx, rdy, sx, sy)
    if abs(den) < EPS:
        return (False, 0.0, ro)

    rx, ry = ro
    t = _cross(ax-rx, ay-ry, sx, sy) / den
    u = _cross(ax-rx, ay-ry, rdx, rdy) / den
    if t >= -EPS and u >= -EPS and u <= 1.0 + EPS:
        px = rx + t*rdx
        py = ry + t*rdy
        return (True, t, (px, py))
    return (False, 0.0, ro)

def first_ray_polygon_hit(ro: Point, rd: Point, poly: Poly) -> Tuple[bool, float, Point]:
    """Return the first intersection of a ray with a polygon boundary."""
    best_t = None
    best_p: Point = ro
    n = len(poly)
    if n < 2:
        return (False, 0.0, ro)
    for i in range(n):
        a = poly[i]
        b = poly[(i+1) % n]
        hit, t, p = ray_segment_intersection(ro, rd, a, b)
        if not hit:
            continue
        if t < EPS:
            continue
        if best_t is None or t < best_t:
            best_t = t
            best_p = p
    if best_t is None:
        return (False, 0.0, ro)
    return (True, float(best_t), best_p)

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
