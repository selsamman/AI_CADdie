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

from engine.prototypes import poly_extrude, regular_octagon_boundary

from engine.features import (
    build_feature_catalog,
    resolve_feature_segment,
    resolve_feature_point,
    resolve_feature_polygon,
    unit_from_dir_token,
    axis_to_dir_token,
    line_intersection,
    ray_polygon_first_hit,
)

from engine.prototypes import dim_lumber_member

Point = Tuple[float,float]


def _resolve_support_objects(scene_constraints: dict, registries: Optional[dict]=None) -> dict:
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
        elif proto == "dim_lumber_member":
            # If already concrete (placement present), we can resolve it for feature lookup.
            if "placement" in params:
                geom = dim_lumber_member.resolve(params, registries)
            else:
                geom = o.get("geom")
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

def compile_scene_constraints(scene_constraints: dict, resolved_scene_for_catalog: Optional[dict]=None, registries: Optional[dict]=None) -> dict:
    """
    Returns an internal-scene-schema dict (compatible with engine.scene.build_scene).
    If resolved_scene_for_catalog is provided, feature catalog validation uses it; else uses the
    constraints scene's objects as-is (for early checking of handles, before operators).
    """
    scene = copy.deepcopy(scene_constraints)

    # If caller provided a resolved scene, validate handles against that.
    # We'll build a progressively-more-resolved scene as we compile objects in order.
    catalog_scene = resolved_scene_for_catalog or _resolve_support_objects(scene, registries)
    obj_index = _index_objects(catalog_scene)
    catalog = build_feature_catalog(catalog_scene)

    def require_handle(handle: str):
        oid, feat = _parse_handle(handle)
        if oid not in obj_index:
            raise ValueError(f"Unknown object id in handle '{handle}'")
        feats = set(next(o["features"] for o in catalog["objects"] if o["id"] == oid))
        if feat not in feats:
            raise ValueError(f"Unknown feature '{feat}' for object '{oid}' in handle '{handle}'")

    def resolve_seg(handle: str):
        require_handle(handle)
        oid, feat = _parse_handle(handle)
        return resolve_feature_segment(obj_index[oid], feat)

    out_objects = []
    # Keep a resolved version of the output objects as we go, so later constraints can
    # reference earlier members (e.g., wing sleepers hitting the hearth sleeper).
    resolved_out_objects: list[dict] = []
    for obj in scene.get("objects", []):
        if obj.get("prototype") != "dim_lumber_member":
            out_objects.append(obj)
            # If we can resolve this object, include it for later feature lookups.
            proto = obj.get("prototype")
            params = obj.get("params", {})
            geom = None
            if proto == "poly_extrude":
                geom = poly_extrude.resolve(params)
            elif proto == "regular_octagon_boundary":
                geom = regular_octagon_boundary.resolve(params)
            elif proto == "dim_lumber_member" and "placement" in params:
                geom = dim_lumber_member.resolve(params, registries)
            ro = copy.deepcopy(obj)
            if geom is not None:
                ro["geom"] = geom
            resolved_out_objects.append(ro)
            obj_index = _index_objects({"objects": resolved_out_objects})
            catalog = build_feature_catalog({"objects": resolved_out_objects})
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

        # Refresh catalogs so we can resolve handles against objects already emitted.
        obj_index = _index_objects({"objects": resolved_out_objects})
        catalog = build_feature_catalog({"objects": resolved_out_objects})

        # --- origin point ---
        origin_kind = origin.get("kind")
        if origin_kind == "offset_from_feature":
            base_handle = origin["feature"]
            base_seg = resolve_seg(base_handle)
            (ax,ay),(bx,by) = base_seg
            mid = ((ax+bx)/2.0, (ay+by)/2.0)

            off_dir = origin["dir"]
            off = float(origin["offset_in"])
            ux,uy = unit_from_dir_token(off_dir)
            origin_pt = (mid[0] + ux*off, mid[1] + uy*off)
        elif origin_kind == "point_on_edge_from_vertex":
            edge_h = origin["edge"]
            vertex_h = origin["vertex"]
            dist = float(origin["distance_in"])
            edge_seg = resolve_seg(edge_h)
            require_handle(vertex_h)
            vo, vf = _parse_handle(vertex_h)
            vpt = resolve_feature_point(obj_index[vo], vf)

            (a,b) = edge_seg
            # Choose which endpoint corresponds to the referenced vertex.
            da = (a[0]-vpt[0])**2 + (a[1]-vpt[1])**2
            db = (b[0]-vpt[0])**2 + (b[1]-vpt[1])**2
            start_end = a if da <= db else b
            other_end = b if da <= db else a
            vx = other_end[0] - start_end[0]
            vy = other_end[1] - start_end[1]
            L = (vx*vx + vy*vy) ** 0.5
            if L <= 1e-9:
                raise ValueError(f"Degenerate edge for '{edge_h}'")
            if dist < -1e-9 or dist > L + 1e-6:
                raise ValueError(f"Distance {dist} is outside edge length {L} for '{edge_h}'")
            ux, uy = vx / L, vy / L
            origin_pt = (start_end[0] + ux*dist, start_end[1] + uy*dist)
        else:
            raise ValueError(f"Unsupported origin kind '{origin_kind}' for dim_lumber_member '{obj['id']}'")

        # Determine member direction token.
        pos_tok = axis_to_dir_token(axis, positive=True)
        dir_tok = pos_tok

        extent_kind = extent.get("kind")

        if extent_kind == "span_between_hits":
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
            length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
            if length <= 1e-9:
                raise ValueError(f"Zero-length span for '{obj['id']}'")

        elif extent_kind == "ray_hit":
            # Ray starts at origin_pt and hits a target feature along extent.dir
            dir_tok = extent["dir"]
            rdx, rdy = unit_from_dir_token(dir_tok)

            until = extent["until"]
            require_handle(until)
            u_oid, u_feat = _parse_handle(until)
            target_obj = obj_index[u_oid]

            # If until is a segment feature, intersect ray with its infinite line.
            # If until is a polygon feature (e.g., footprint), hit the boundary.
            hit_pt: Optional[Point] = None
            try:
                seg = resolve_feature_segment(target_obj, u_feat)
                hit = ray_segment_first_hit(origin_pt, (rdx, rdy), seg)
                hit_pt = hit[1] if hit else None
            except Exception:
                poly = resolve_feature_polygon(target_obj, u_feat)
                hit_pt = ray_polygon_first_hit(origin_pt, (rdx, rdy), poly)

            if hit_pt is None:
                raise ValueError(f"Could not ray-hit '{until}' from '{obj['id']}'")

            start = origin_pt
            end = hit_pt
            length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
            if length <= 1e-9:
                raise ValueError(f"Zero-length ray for '{obj['id']}'")

        else:
            raise ValueError(f"Unsupported extent kind '{extent_kind}' for dim_lumber_member '{obj['id']}'")

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
        out_objects.append(new_obj)

        # Resolve and store for later feature references.
        resolved_obj = copy.deepcopy(new_obj)
        try:
            resolved_obj["geom"] = dim_lumber_member.resolve(new_params, registries)
        except Exception:
            # Leave unresolved; later constraints may not require it.
            pass
        resolved_out_objects.append(resolved_obj)

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
