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
from typing import Dict, Any, Tuple, Optional
import copy

from engine.prototypes import poly_extrude, regular_octagon_boundary, dim_lumber_member

from engine.features import (
    build_feature_catalog,
    resolve_feature_segment,
    resolve_feature_point,
    resolve_feature_polygon,
    unit_from_dir_token,
    axis_to_dir_token,
    line_intersection,
    ray_segment_intersection,
    ray_polygon_intersection,
)

Point = Tuple[float,float]


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
    resolved_scene_for_catalog: Optional[dict]=None,
    registries: Optional[dict]=None,
) -> dict:
    """
    Returns an internal-scene-schema dict (compatible with engine.scene.build_scene).
    If resolved_scene_for_catalog is provided, feature catalog validation uses it; else uses the
    constraints scene's objects as-is (for early checking of handles, before operators).
    """
    scene = copy.deepcopy(scene_constraints)

    # We'll compile in object order, progressively resolving objects so later constraints can
    # reference earlier objects (e.g., wing sleepers intersecting the hearth sleeper).
    catalog_scene = resolved_scene_for_catalog or _resolve_support_objects(scene)
    obj_index = _index_objects(catalog_scene)
    catalog = build_feature_catalog(catalog_scene)

    def require_handle(handle: str):
        oid, feat = _parse_handle(handle)
        if oid not in obj_index:
            raise ValueError(f"Unknown object id in handle '{handle}'")
        feats = set(next(o["features"] for o in catalog["objects"] if o["id"] == oid))
        if feat not in feats:
            raise ValueError(f"Unknown feature '{feat}' for object '{oid}' in handle '{handle}'")

    def refresh_catalog():
        nonlocal catalog
        catalog = build_feature_catalog({"objects": list(obj_index.values())})

    def resolve_seg(handle: str):
        require_handle(handle)
        oid, feat = _parse_handle(handle)
        return resolve_feature_segment(obj_index[oid], feat)

    def resolve_pt(handle: str):
        require_handle(handle)
        oid, feat = _parse_handle(handle)
        return resolve_feature_point(obj_index[oid], feat)

    def resolve_poly(handle: str):
        require_handle(handle)
        oid, feat = _parse_handle(handle)
        return resolve_feature_polygon(obj_index[oid], feat)

    def resolve_point_like(spec: dict) -> Point:
        kind = spec.get("kind")
        if kind == "offset_from_feature":
            base_handle = spec["feature"]
            base_seg = resolve_seg(base_handle)
            (ax,ay),(bx,by) = base_seg
            mid = ((ax+bx)/2.0, (ay+by)/2.0)
            ux,uy = unit_from_dir_token(spec["dir"])
            off = float(spec["offset_in"])
            return (mid[0] + ux*off, mid[1] + uy*off)

        if kind == "point_on_edge_from_vertex":
            edge_handle = spec["edge"]
            vertex_handle = spec["vertex"]
            dist = float(spec["distance_in"])
            (a,b) = resolve_seg(edge_handle)
            v = resolve_pt(vertex_handle)
            # Determine which endpoint matches the referenced vertex
            def _close(p: Point, q: Point) -> bool:
                return ((p[0]-q[0])**2 + (p[1]-q[1])**2) ** 0.5 < 1e-6
            if _close(a, v):
                start = a
                end = b
            elif _close(b, v):
                start = b
                end = a
            else:
                raise ValueError(f"Vertex '{vertex_handle}' is not an endpoint of edge '{edge_handle}'")
            vx,vy = (end[0]-start[0], end[1]-start[1])
            L = (vx*vx + vy*vy) ** 0.5
            if L <= 1e-9:
                raise ValueError(f"Degenerate edge '{edge_handle}'")
            if dist < -1e-9 or dist - L > 1e-6:
                raise ValueError(f"distance_in={dist} exceeds edge length {L} on '{edge_handle}'")
            ux,uy = (vx/L, vy/L)
            return (start[0] + ux*dist, start[1] + uy*dist)

        if kind == "xy":
            xy = spec.get("xy")
            if not (isinstance(xy, list) and len(xy) == 2):
                raise ValueError("xy must be [x,y]")
            return (float(xy[0]), float(xy[1]))

        raise ValueError(f"Unsupported point kind '{kind}'")

    out_objects = []
    for obj in scene.get("objects", []):
        if obj.get("prototype") != "dim_lumber_member":
            out_objects.append(obj)
            # Keep catalog updated for later references
            if obj.get("id") and obj.get("geom") is not None:
                obj_index[obj["id"]] = obj
                refresh_catalog()
            continue

        params = obj.get("params", {})
        placement_c = params.get("placement_constraints")
        if not placement_c:
            out_objects.append(obj)
            continue

        axis = placement_c["axis"]  # e.g., "E-W"
        origin = placement_c["origin"]
        extent = placement_c["extent"]

        # Direction token along member length (optional override)
        pos_tok = placement_c.get("direction") or axis_to_dir_token(axis, positive=True)
        dx,dy = unit_from_dir_token(pos_tok)

        origin_pt = resolve_point_like(origin)

        # Build an infinite line along the axis passing through origin_pt
        line_p1 = origin_pt
        line_p2 = (origin_pt[0] + dx, origin_pt[1] + dy)

        # Resolve extent
        start: Point
        end: Point
        if extent.get("kind") == "span_between_hits":
            h_from = extent["from"]
            h_to = extent["to"]
            seg_from = resolve_seg(h_from)
            seg_to = resolve_seg(h_to)

            hit_from = line_intersection(line_p1, line_p2, seg_from[0], seg_from[1])
            hit_to = line_intersection(line_p1, line_p2, seg_to[0], seg_to[1])
            if hit_from is None or hit_to is None:
                raise ValueError(f"Could not intersect axis line for '{obj['id']}' with extent '{h_from}', '{h_to}'")
            start = hit_from
            end = hit_to

        elif extent.get("kind") == "ray_hit":
            start = origin_pt
            until = extent["until"]
            require_handle(until)
            oid, feat = _parse_handle(until)
            if feat == "footprint":
                poly = resolve_poly(until)
                hit = ray_polygon_intersection(start, (dx,dy), poly)
                if hit is None:
                    raise ValueError(f"Ray from '{obj['id']}' did not hit polygon '{until}'")
                end = hit
            else:
                seg = resolve_seg(until)
                hit = ray_segment_intersection(start, (dx,dy), seg[0], seg[1])
                if hit is None:
                    raise ValueError(f"Ray from '{obj['id']}' did not hit segment '{until}'")
                end = hit[0]
        else:
            raise ValueError(f"Unsupported extent kind '{extent.get('kind')}' for dim_lumber_member '{obj['id']}'")

        length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        if length <= 1e-9:
            raise ValueError(f"Zero-length member for '{obj['id']}'")

        # Emit internal placement params
        new_params = copy.deepcopy(params)
        new_params.pop("placement_constraints", None)
        new_params["placement"] = {
            "start": [float(start[0]), float(start[1])],
            # dim_lumber_member currently expects a direction token, not a vector.
            "direction": pos_tok,
            "length": float(length),
        }
        new_obj = copy.deepcopy(obj)
        new_obj["params"] = new_params
        out_objects.append(new_obj)

        # Add to catalog scene for later references (requires registries to resolve profile)
        if registries is not None:
            geom = dim_lumber_member.resolve(new_params, registries)
            cat_obj = copy.deepcopy(new_obj)
            cat_obj["geom"] = geom
            obj_index[new_obj["id"]] = cat_obj
            refresh_catalog()

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
