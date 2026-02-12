"""
Compile LLM-facing "scene constraints" into the internal scene schema.

The constraints format is intentionally small and token-based. This compiler:
- validates references against a generated feature catalog (runtime)
- expands constraints into numeric placements compatible with existing prototypes

NOTE: This is an incremental implementation. Currently supported:
- dim_lumber_member placement with:
  - origin: offset_from_feature
  - axis: E-W / N-S / NE-SW / NW-SE
  - extent: span_between_hits (between two wall/face features)

This already covers the "Hearth Sleeper ... 2 inches south of ... extends to East/West wall"
pattern in the updated spec.
"""
from __future__ import annotations
from typing import Dict, Any, Tuple, Optional, List
import copy
import math

from engine.prototypes import poly_extrude, regular_octagon_boundary, dim_lumber_member

from engine.features import (
    list_features_for_object,
    resolve_feature_point,
    resolve_feature_segment,
    resolve_feature_polygon,
    unit_from_dir_token,
    axis_to_dir_token,
    line_intersection,
)

Point = Tuple[float,float]


def _cross(ax: float, ay: float, bx: float, by: float) -> float:
    return ax * by - ay * bx


def _ray_segment_first_hit(ray_o: Point, ray_d: Point, seg: Tuple[Point, Point]) -> Optional[Point]:
    """Return intersection point of ray with segment, if any, preferring the nearest hit."""
    (ox, oy) = ray_o
    (dx, dy) = ray_d
    (p, q) = seg
    (px, py) = p
    (qx, qy) = q

    sx = qx - px
    sy = qy - py
    denom = _cross(dx, dy, sx, sy)
    if abs(denom) < 1e-9:
        return None

    rx = px - ox
    ry = py - oy
    t = _cross(rx, ry, sx, sy) / denom
    u = _cross(rx, ry, dx, dy) / denom
    if t < -1e-9:
        return None
    if u < -1e-9 or u > 1.0 + 1e-9:
        return None

    return (ox + t * dx, oy + t * dy)


def _ray_polygon_first_hit(ray_o: Point, ray_d: Point, poly: List[Point]) -> Optional[Point]:
    """Return nearest intersection point of a ray with a polygon boundary."""
    best: Optional[Point] = None
    best_t: float = float("inf")
    (ox, oy) = ray_o
    (dx, dy) = ray_d

    n = len(poly)
    if n < 3:
        return None

    for i in range(n):
        a = poly[i]
        b = poly[(i + 1) % n]
        hit = _ray_segment_first_hit(ray_o, ray_d, (a, b))
        if hit is None:
            continue
        t = (hit[0] - ox) * dx + (hit[1] - oy) * dy
        if t >= -1e-9 and t < best_t:
            best_t = t
            best = hit
    return best


def _resolve_support_objects(scene_constraints: dict) -> dict:
    """
    Produce a shallow "resolved" scene containing geom for non-template, non-operator objects,
    sufficient for feature geometry during compilation.
    """
    out = {"objects": []}
    for o in scene_constraints.get("objects", []):
        proto = o.get("prototype")
        params = o.get("params", {})
        if proto == "poly_extrude":
            geom = poly_extrude.resolve(params)
        elif proto == "regular_octagon_boundary":
            geom = regular_octagon_boundary.resolve(params)
        else:
            # Leave unresolved; may not be needed for compilation.
            geom = o.get("geom")
        oo = copy.deepcopy(o)
        if geom is not None:
            oo["geom"] = geom
        out["objects"].append(oo)
    return out

def _index_objects(scene: dict) -> Dict[str, dict]:
    return {o["id"]: o for o in scene.get("objects", [])}

def _parse_handle(handle: str) -> Tuple[str, str]:
    """
    Handle form: "ObjectId.featureString"
    Example: "Octagon.wall:West" or "NewHearth.face:front"
    """
    if "." not in handle:
        raise ValueError(f"Invalid feature handle '{handle}'. Expected 'ObjectId.<feature>'")
    oid, feat = handle.split(".", 1)
    return oid, feat

def compile_scene_constraints(
    scene_constraints: dict,
    registries: Optional[dict] = None,
    resolved_scene_for_catalog: Optional[dict]=None,
) -> dict:
    """
    Returns an internal-scene-schema dict (compatible with engine.scene.build_scene).
    If resolved_scene_for_catalog is provided, feature catalog validation uses it; else uses the
    constraints scene's objects as-is (for early checking of handles, before operators).
    """
    scene = copy.deepcopy(scene_constraints)

    # Build an index we can update as we compile objects in order.
    # Start with whatever the caller provided, else resolve only simple geometry
    # (room boundaries, poly extrudes) so their features are available.
    catalog_scene = resolved_scene_for_catalog or _resolve_support_objects(scene)
    obj_index = _index_objects(catalog_scene)

    def require_handle(handle: str):
        oid, feat = _parse_handle(handle)
        if oid not in obj_index:
            raise ValueError(f"Unknown object id in handle '{handle}'")
        feats = set(list_features_for_object(obj_index[oid]))
        if feat not in feats:
            raise ValueError(f"Unknown feature '{feat}' for object '{oid}' in handle '{handle}'")

    def resolve_seg(handle: str):
        require_handle(handle)
        oid, feat = _parse_handle(handle)
        return resolve_feature_segment(obj_index[oid], feat)

    def resolve_pt(handle: str):
        require_handle(handle)
        oid, feat = _parse_handle(handle)
        return resolve_feature_point(obj_index[oid], feat)

    out_objects = []
    for obj in scene.get("objects", []):
        if obj.get("prototype") != "dim_lumber_member":
            out_objects.append(obj)
            continue

        params = obj.get("params", {})
        placement_c = params.get("placement_constraints")
        if not placement_c:
            out_objects.append(obj)
            continue

        axis = placement_c["axis"]  # e.g., "E-W"
        origin = placement_c["origin"]  # constraint object
        extent = placement_c["extent"]  # constraint object
        reference_edge = placement_c.get("reference_edge")

        # --- origin point ---
        okind = origin.get("kind")
        if okind == "offset_from_feature":
            base_handle = origin["feature"]
            base_seg = resolve_seg(base_handle)
            (ax,ay),(bx,by) = base_seg
            mid = ((ax+bx)/2.0, (ay+by)/2.0)

            off_dir = origin["dir"]
            off = float(origin["offset_in"])
            ux,uy = unit_from_dir_token(off_dir)
            origin_pt = (mid[0] + ux*off, mid[1] + uy*off)

        elif okind == "point_on_edge_from_vertex":
            edge_handle = origin["edge"]
            vert_handle = origin["vertex"]
            dist_in = float(origin["distance_in"])

            seg = resolve_seg(edge_handle)
            vpt = resolve_pt(vert_handle)
            (p0x,p0y),(p1x,p1y) = seg

            # Choose segment endpoint closest to the referenced vertex.
            d0 = ((p0x - vpt[0])**2 + (p0y - vpt[1])**2) ** 0.5
            d1 = ((p1x - vpt[0])**2 + (p1y - vpt[1])**2) ** 0.5
            if d0 <= d1:
                start_pt = (p0x, p0y)
                other_pt = (p1x, p1y)
            else:
                start_pt = (p1x, p1y)
                other_pt = (p0x, p0y)

            ex = other_pt[0] - start_pt[0]
            ey = other_pt[1] - start_pt[1]
            elen = (ex*ex + ey*ey) ** 0.5
            if elen <= 1e-9:
                raise ValueError(f"Edge '{edge_handle}' for '{obj['id']}' has zero length")
            if dist_in < -1e-9 or dist_in > elen + 1e-6:
                raise ValueError(
                    f"distance_in={dist_in} out of range for '{obj['id']}' along edge '{edge_handle}' (len={elen})"
                )
            t = max(0.0, min(1.0, dist_in / elen))
            origin_pt = (start_pt[0] + ex*t, start_pt[1] + ey*t)

        else:
            raise ValueError(f"Unsupported origin kind '{okind}' for dim_lumber_member '{obj['id']}'")

        # By default, use the + axis direction for span lengths.
        pos_tok = axis_to_dir_token(axis, positive=True)

        ekind = extent.get("kind")
        if ekind == "span_between_hits":
            # Build an infinite line along the axis passing through origin_pt
            dx,dy = unit_from_dir_token(pos_tok)
            line_p1 = origin_pt
            line_p2 = (origin_pt[0] + dx, origin_pt[1] + dy)

            h_from = extent["from"]
            h_to = extent["to"]
            seg_from = resolve_seg(h_from)
            seg_to = resolve_seg(h_to)

            hit_from = line_intersection(line_p1, line_p2, seg_from[0], seg_from[1])
            hit_to = line_intersection(line_p1, line_p2, seg_to[0], seg_to[1])
            if hit_from is None or hit_to is None:
                raise ValueError(f"Could not intersect axis line for '{obj['id']}' with extent walls '{h_from}', '{h_to}'")

            start = hit_from
            end = hit_to
            dir_tok = pos_tok

        elif ekind == "ray_hit":
            # Cast ray from origin_pt in the requested direction until it hits the target feature.
            dir_tok = str(placement_c.get("direction") or pos_tok)
            rdx,rdy = unit_from_dir_token(dir_tok)

            until_handle = extent["until"]
            # First try a segment feature; if not segment, treat as polygon feature.
            hit: Optional[Point] = None
            try:
                seg = resolve_seg(until_handle)
                hit = _ray_segment_first_hit(origin_pt, (rdx, rdy), seg)
            except ValueError:
                # Polygon feature (typically footprint)
                require_handle(until_handle)
                oid, feat = _parse_handle(until_handle)
                poly = resolve_feature_polygon(obj_index[oid], feat)
                hit = _ray_polygon_first_hit(origin_pt, (rdx, rdy), [(float(x), float(y)) for x,y in poly])

            if hit is None:
                raise ValueError(f"ray_hit for '{obj['id']}' did not intersect '{until_handle}'")

            start = origin_pt
            end = hit

        else:
            raise ValueError(f"Unsupported extent kind '{ekind}' for dim_lumber_member '{obj['id']}'")

        length = math.hypot(end[0] - start[0], end[1] - start[1])
        if length <= 1e-9:
            raise ValueError(f"Zero-length span for '{obj['id']}'")

        # Emit internal placement params
        new_params = copy.deepcopy(params)
        new_params.pop("placement_constraints", None)
        new_params["placement"] = {
            "start": [float(start[0]), float(start[1])],
            # dim_lumber_member currently expects a direction token, not a vector.
            "direction": dir_tok,
            "length": float(length),
        }
        if reference_edge:
            new_params["placement"]["reference_edge"] = reference_edge
        new_obj = copy.deepcopy(obj)
        new_obj["params"] = new_params

        # If we can resolve this member now, attach geom so later constraints can reference
        # features like footprint (e.g., ray_hit until HearthSleeper.footprint).
        if registries is not None:
            try:
                new_obj["geom"] = dim_lumber_member.resolve(new_params, registries)
            except Exception:
                # Leave unresolved; downstream build_scene will surface the error.
                pass

        out_objects.append(new_obj)
        obj_index[new_obj["id"]] = new_obj

    out = copy.deepcopy(scene)
    out["objects"] = out_objects

    # Internal scene schema expects anchor_id. If missing in constraints input, choose a
    # sensible default: prefer the first room boundary-like object.
    if "anchor_id" not in out:
        for o in out_objects:
            if o.get("prototype") == "regular_octagon_boundary":
                out["anchor_id"] = o.get("id")
                break
        else:
            if out_objects:
                out["anchor_id"] = out_objects[0].get("id")

    return out
