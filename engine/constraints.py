"""Compile LLM-facing 'scene constraints' into the internal scene schema.

This compiler keeps the constraints format small (tokens + feature handles) and expands it into
numeric placements compatible with existing prototypes.

Supported (current):
- dim_lumber_member with params.placement_constraints:
  - axis: E-W | N-S | NE-SW | NW-SE
  - origin:
      - offset_from_feature
      - point_on_edge_from_vertex
  - extent:
      - span_between_hits
      - ray_hit
  - optional: reference_edge (forwarded; may be used by downstream resolver if supported)
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
    ray_segment_first_hit,
    ray_polygon_first_hit,
)

Point = Tuple[float, float]


def _resolve_support_objects(scene_constraints: dict) -> dict:
    """Resolve only prototypes needed for feature geometry during compilation."""
    out = {"objects": []}
    for o in scene_constraints.get("objects", []):
        proto = o.get("prototype")
        params = o.get("params", {})
        geom = None
        if proto == "poly_extrude":
            geom = poly_extrude.resolve(params)
        elif proto == "regular_octagon_boundary":
            geom = regular_octagon_boundary.resolve(params)
        oo = copy.deepcopy(o)
        if geom is not None:
            oo["geom"] = geom
        out["objects"].append(oo)
    return out


def _index_objects(scene: dict) -> Dict[str, dict]:
    return {o["id"]: o for o in scene.get("objects", [])}


def _parse_handle(handle: str) -> Tuple[str, str]:
    if "." not in handle:
        raise ValueError(f"Invalid feature handle '{handle}'. Expected 'ObjectId.<feature>'")
    oid, feat = handle.split(".", 1)
    return oid, feat


def compile_scene_constraints(scene_constraints: dict, registries: Optional[dict] = None) -> dict:
    scene = copy.deepcopy(scene_constraints)

    # Only compile if it's clearly constraints-authored.
    if not (
        scene.get("scene_type") == "constraints"
        or any(
            o.get("prototype") == "dim_lumber_member"
            and isinstance(o.get("params", {}).get("placement_constraints"), dict)
            for o in scene.get("objects", [])
        )
    ):
        return scene

    support = _resolve_support_objects(scene)
    obj_index = _index_objects(support)

    # Build feature catalog from currently-known geometry.
    catalog = build_feature_catalog(support)
    feat_map = {o['id']: o.get('features', []) for o in catalog.get('objects', [])}

    def require_handle(handle: str):
        oid, feat = _parse_handle(handle)
        if oid not in obj_index:
            raise ValueError(f"Unknown object id in handle '{handle}'")
        # runtime validate feature name against catalog list
        feats = feat_map.get(oid, [])
        if feat not in feats:
            raise ValueError(f"Unknown feature '{feat}' for object '{oid}' (handle '{handle}')")

    def resolve_seg(handle: str):
        require_handle(handle)
        oid, feat = _parse_handle(handle)
        return resolve_feature_segment(obj_index[oid], feat)

    # compile objects in order; when registries provided, we can resolve dim_lumber as we go to
    # support later ray hits against previous members' footprints.
    concrete_objects = []
    for o in scene.get("objects", []):
        if o.get("prototype") != "dim_lumber_member":
            concrete_objects.append(o)
            continue

        params = copy.deepcopy(o.get("params", {}))
        pc = params.pop("placement_constraints", None)
        if not isinstance(pc, dict):
            concrete_objects.append(o)
            continue

        axis = str(pc.get("axis", "E-W")).upper()
        origin = pc.get("origin") or {}
        extent = pc.get("extent") or {}
        ref_edge = pc.get("reference_edge")

        # --- origin ---
        kind = origin.get("kind")
        if kind == "offset_from_feature":
            feature_h = origin["feature"]
            require_handle(feature_h)
            oid, feat = _parse_handle(feature_h)
            seg = resolve_feature_segment(obj_index[oid], feat)
            a, b = seg
            # feature normal direction is provided as a token (N/S/E/W/NE/etc)
            dir_tok = str(origin.get("dir", "S"))
            ux, uy = unit_from_dir_token(dir_tok)
            off = float(origin.get("offset_in", 0.0))
            # choose midpoint of the segment and offset from it
            mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
            origin_pt = (mx + ux * off, my + uy * off)

        elif kind == "point_on_edge_from_vertex":
            edge_h = origin["edge"]
            vertex_h = origin["vertex"]
            dist = float(origin["distance_in"])
            edge_seg = resolve_seg(edge_h)

            require_handle(vertex_h)
            vo, vf = _parse_handle(vertex_h)
            vpt = resolve_feature_point(obj_index[vo], vf)

            a, b = edge_seg
            da = (a[0] - vpt[0]) ** 2 + (a[1] - vpt[1]) ** 2
            db = (b[0] - vpt[0]) ** 2 + (b[1] - vpt[1]) ** 2
            start_pt = a if da <= db else b
            end_pt = b if da <= db else a

            vx, vy = (end_pt[0] - start_pt[0], end_pt[1] - start_pt[1])
            L = (vx * vx + vy * vy) ** 0.5
            if L <= 1e-9:
                raise ValueError(f"Zero-length edge '{edge_h}' for origin of '{o['id']}'")
            ux, uy = (vx / L, vy / L)
            if dist < -1e-9 or dist > L + 1e-6:
                raise ValueError(
                    f"distance_in={dist} is out of range for edge '{edge_h}' (length={L}) in '{o['id']}'"
                )
            origin_pt = (start_pt[0] + ux * dist, start_pt[1] + uy * dist)

        else:
            raise ValueError(f"Unsupported origin kind '{kind}' for dim_lumber_member '{o['id']}'")

        # --- axis line (infinite) through origin ---
        pos_tok = axis_to_dir_token(axis, positive=True)
        dx, dy = unit_from_dir_token(pos_tok)
        line_p1 = origin_pt
        line_p2 = (origin_pt[0] + dx, origin_pt[1] + dy)

        # --- extent ---
        ek = extent.get("kind")
        if ek == "span_between_hits":
            h_from = extent["from"]
            h_to = extent["to"]
            seg_from = resolve_seg(h_from)
            seg_to = resolve_seg(h_to)
            hit_from = line_intersection(line_p1, line_p2, seg_from[0], seg_from[1])
            hit_to = line_intersection(line_p1, line_p2, seg_to[0], seg_to[1])
            if hit_from is None or hit_to is None:
                raise ValueError(
                    f"Could not intersect axis line for '{o['id']}' with extent walls '{h_from}', '{h_to}'"
                )
            start = hit_from
            end = hit_to

        elif ek == "ray_hit":
            dir_tok = str(extent.get("dir", pc.get("direction", pos_tok)))
            udir = unit_from_dir_token(dir_tok)
            until_h = extent["until"]
            require_handle(until_h)
            uoid, ufeat = _parse_handle(until_h)
            target_obj = obj_index[uoid]

            # try segment first, then polygon
            pt = None
            try:
                seg = resolve_feature_segment(target_obj, ufeat)
                pt = ray_segment_first_hit(origin_pt, udir, seg)
            except Exception:
                seg = None
            if pt is None:
                poly = resolve_feature_polygon(target_obj, ufeat)
                pt = ray_polygon_first_hit(origin_pt, udir, poly)
            if pt is None:
                raise ValueError(f"Ray from '{o['id']}' did not hit '{until_h}'")

            start = origin_pt
            end = pt

        else:
            raise ValueError(f"Unsupported extent kind '{ek}' for dim_lumber_member '{o['id']}'")

        # convert start/end to start+length+direction as expected by prototype
        # Determine direction token along axis from start->end
        vx, vy = (end[0] - start[0], end[1] - start[1])
        length = (vx * vx + vy * vy) ** 0.5
        if length <= 1e-6:
            raise ValueError(f"Computed zero length for '{o['id']}' from constraints")
        # choose direction token closest to vx,vy among the 8 cardinal tokens
        # use axis positive token as default
        # choose direction: prefer explicit placement constraint, else infer from start->end
        if pc.get('direction'):
            direction = pc.get('direction')
        else:
            # pick axis token matching start->end vector
            ax_u = unit_from_dir_token(pos_tok)
            dot = vx*ax_u[0] + vy*ax_u[1]
            neg_tok = axis_to_dir_token(axis, positive=False)
            direction = pos_tok if dot >= 0 else neg_tok

        params.setdefault("placement", {})
        params["placement"]["start"] = [float(start[0]), float(start[1])]
        params["placement"]["direction"] = direction
        params["placement"]["length"] = float(length)
        if ref_edge is not None:
            params["placement"]["reference_edge"] = ref_edge

        new_obj = copy.deepcopy(o)
        new_obj["params"] = params
        # If registries supplied, resolve now so later features can reference this member's footprint
        if registries is not None:
            try:
                geom = dim_lumber_member.resolve(params, registries)
                new_obj["geom"] = geom
                # update support index + catalog to allow later handle validation/hits
                obj_index[new_obj["id"]] = new_obj
                support.setdefault("objects", []).append(new_obj)
                catalog = build_feature_catalog(support)
                feat_map.update({oo['id']: oo.get('features', []) for oo in catalog.get('objects', [])})
            except Exception:
                # Leave unresolved; build_scene will error later if invalid.
                pass

        concrete_objects.append(new_obj)

    scene["objects"] = concrete_objects
    scene["scene_type"] = "internal"
    return scene