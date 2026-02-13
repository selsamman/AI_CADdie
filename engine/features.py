"""
Feature catalog + lightweight feature geometry resolver.

This module intentionally does NOT hard-code prototype-specific feature enums
into JSON Schema. Instead prototypes publish feature handle strings, and we
validate those handles at runtime.

Feature geometry in this file is "plan space" only for now (2D).
"""
from __future__ import annotations

from typing import Dict, List, Tuple, Optional, Any
import math

Point = Tuple[float, float]
Segment = Tuple[Point, Point]
Poly = List[Point]

CARDINAL_WALLS_CW = ["North","NorthEast","East","SouthEast","South","SouthWest","West","NorthWest"]
CARDINAL_VERTS_CW = ["North","NorthEast","East","SouthEast","South","SouthWest","West","NorthWest"]

def _bbox(poly: Poly) -> Tuple[float,float,float,float]:
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)

def list_features_for_object(obj: dict) -> List[str]:
    """Return a list of supported feature handle strings for a *resolved* object."""
    proto = obj.get("prototype")
    geom = obj.get("geom", {})
    feats: List[str] = ["footprint"]
    if proto == "regular_octagon_boundary":
        feats += [f"wall:{n}" for n in CARDINAL_WALLS_CW]
        feats += [f"vertex:{n}" for n in CARDINAL_VERTS_CW]
    elif proto == "poly_extrude":
        # For now: bbox-derived faces in plan.
        feats += ["face:front","face:back","face:left","face:right","center"]
    elif proto == "dim_lumber_member":
        feats += ["centerline","start","end"]
    return feats

def build_feature_catalog(resolved_scene: dict) -> dict:
    objs = []
    for o in resolved_scene.get("objects", []):
        objs.append({
            "id": o["id"],
            "prototype": o.get("prototype"),
            "features": list_features_for_object(o),
        })
    return {
        "objects": objs,
        "directions": ["N","NE","E","SE","S","SW","W","NW"],
        "axes": ["N-S","E-W","NE-SW","NW-SE"],
    }

def _require_feature(obj: dict, feature: str):
    feats = set(list_features_for_object(obj))
    if feature not in feats:
        raise ValueError(f"Object '{obj['id']}' (prototype={obj.get('prototype')}) does not support feature '{feature}'")

def resolve_feature_point(obj: dict, feature: str) -> Point:
    """Resolve a feature handle to a point in plan space."""
    _require_feature(obj, feature)
    proto = obj.get("prototype")
    geom = obj.get("geom", {})
    if feature == "center":
        poly = geom["footprint"]
        mnx,mny,mxx,mxy = _bbox(poly)
        return ((mnx+mxx)/2.0, (mny+mxy)/2.0)
    if proto == "regular_octagon_boundary" and feature.startswith("vertex:"):
        name = feature.split(":",1)[1]
        idx = CARDINAL_VERTS_CW.index(name)
        # Vertex name is defined as the junction between wall idx and next wall clockwise.
        # In the local vertex order produced by the prototype, that is vertex (idx+1) mod 8.
        poly = geom["footprint"]
        return poly[(idx+1) % 8]
    if proto == "dim_lumber_member":
        if feature == "start":
            return tuple(geom["start"])  # type: ignore
        if feature == "end":
            return tuple(geom["end"])  # type: ignore
    raise ValueError(f"Feature '{feature}' is not a point feature for object '{obj['id']}'")

def resolve_feature_segment(obj: dict, feature: str) -> Segment:
    """Resolve a feature handle to a segment in plan space (finite segment)."""
    _require_feature(obj, feature)
    proto = obj.get("prototype")
    geom = obj.get("geom", {})
    if proto == "regular_octagon_boundary" and feature.startswith("wall:"):
        name = feature.split(":",1)[1]
        i = CARDINAL_WALLS_CW.index(name)
        poly = geom["footprint"]
        a = poly[i]
        b = poly[(i+1) % 8]
        return (a,b)
    if proto == "poly_extrude" and feature.startswith("face:"):
        poly = geom["footprint"]
        mnx,mny,mxx,mxy = _bbox(poly)
        f = feature.split(":",1)[1]
        if f == "front":   # max y
            return ((mnx,mxy),(mxx,mxy))
        if f == "back":    # min y
            return ((mnx,mny),(mxx,mny))
        if f == "left":    # min x
            return ((mnx,mny),(mnx,mxy))
        if f == "right":   # max x
            return ((mxx,mny),(mxx,mxy))
    raise ValueError(f"Feature '{feature}' is not a segment feature for object '{obj['id']}'")

def resolve_feature_polygon(obj: dict, feature: str) -> Poly:
    _require_feature(obj, feature)
    if feature == "footprint":
        return obj["geom"]["footprint"]
    raise ValueError(f"Feature '{feature}' is not a polygon feature for object '{obj['id']}'")

def unit_from_dir_token(tok: str) -> Point:
    tok = tok.upper()
    mapping = {
        "N": (0.0, 1.0),
        "NE": (1.0, 1.0),
        "E": (1.0, 0.0),
        "SE": (1.0, -1.0),
        "S": (0.0, -1.0),
        "SW": (-1.0, -1.0),
        "W": (-1.0, 0.0),
        "NW": (-1.0, 1.0),
    }
    if tok not in mapping:
        raise ValueError(f"Unknown direction token '{tok}'")
    x,y = mapping[tok]
    L = math.hypot(x,y)
    return (x/L, y/L)

def axis_to_dir_token(axis: str, positive: bool=True) -> str:
    axis = axis.upper()
    if axis == "E-W":
        return "E" if positive else "W"
    if axis == "N-S":
        return "N" if positive else "S"
    if axis == "NE-SW":
        return "NE" if positive else "SW"
    if axis == "NW-SE":
        return "NW" if positive else "SE"
    raise ValueError(f"Unknown axis '{axis}'")

def line_intersection(p1: Point, p2: Point, p3: Point, p4: Point) -> Optional[Point]:
    """
    Intersection of infinite lines (p1,p2) and (p3,p4).
    Returns None if parallel (or numerically close).
    """
    x1,y1 = p1; x2,y2 = p2; x3,y3 = p3; x4,y4 = p4
    den = (x1-x2)*(y3-y4) - (y1-y2)*(x3-x4)
    if abs(den) < 1e-9:
        return None
    px = ((x1*y2 - y1*x2)*(x3-x4) - (x1-x2)*(x3*y4 - y3*x4)) / den
    py = ((x1*y2 - y1*x2)*(y3-y4) - (y1-y2)*(x3*y4 - y3*x4)) / den
    return (px,py)

# --- Ray intersection helpers (plan view) ---
def _ray_intersect_segment(origin: Point, dir_u: Point, a: Point, b: Point) -> Optional[Tuple[float, Point]]:
    """Return (t, point) for intersection of ray origin+t*dir_u (t>=0) with segment a-b, or None."""
    ox, oy = origin; dx, dy = dir_u; x1,y1=a; x2,y2=b
    # Solve origin + t*d = a + u*(b-a), with t>=0 and u in [0,1]
    rx, ry = dx, dy
    sx, sy = x2-x1, y2-y1
    den = rx*sy - ry*sx
    if abs(den) < 1e-9:
        return None
    qpx, qpy = x1-ox, y1-oy
    t = (qpx*sy - qpy*sx) / den
    u = (qpx*ry - qpy*rx) / den
    if t < -1e-9 or u < -1e-9 or u > 1+1e-9:
        return None
    pt = (ox + t*dx, oy + t*dy)
    return (t, pt)

def ray_segment_first_hit(origin: Point, dir_u: Point, seg: Tuple[Point,Point]) -> Optional[Point]:
    hit = _ray_intersect_segment(origin, dir_u, seg[0], seg[1])
    return None if hit is None else hit[1]

def ray_polygon_first_hit(origin: Point, dir_u: Point, poly: list[Point]) -> Optional[Point]:
    """Return closest intersection point of ray with polygon boundary, or None."""
    best_t = None
    best_pt = None
    n = len(poly)
    if n < 2:
        return None
    for i in range(n):
        a = poly[i]
        b = poly[(i+1)%n]
        hit = _ray_intersect_segment(origin, dir_u, a, b)
        if hit is None:
            continue
        t, pt = hit
        if t < 1e-9:
            continue
        if best_t is None or t < best_t:
            best_t = t
            best_pt = pt
    return best_pt