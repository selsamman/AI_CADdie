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
from engine.geom import clip_halfplane, ray_segment_intersection

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


def _member_half_width_on_floor(params: Dict[str, Any], registries: Dict[str, Any] | None) -> float:
    """Return half the member footprint width (in plan) in inches.

    Matches dim_lumber_member.resolve: if wide_face is down/up/flat => width_on_floor = w,
    if side/edge => width_on_floor = t.
    """
    t, w = dim_lumber_member._resolve_profile(params, registries)  # type: ignore[attr-defined]
    orient = params.get("orientation", {}) or {}
    wide_face = str(orient.get("wide_face", "down")).strip().lower()
    if wide_face in ("down", "up", "flat"):
        width_on_floor = w
    elif wide_face in ("side", "edge"):
        width_on_floor = t
    else:
        raise ValueError("orientation.wide_face must be one of: down/up/flat/side/edge")
    return float(width_on_floor) / 2.0


def _member_width_and_height(params: Dict[str, Any], registries: Dict[str, Any] | None) -> Tuple[float, float]:
    """Return (width_on_floor, height) in inches for a dim_lumber_member."""
    t, w = dim_lumber_member._resolve_profile(params, registries)  # type: ignore[attr-defined]
    orient = params.get("orientation", {}) or {}
    wide_face = str(orient.get("wide_face", "down")).strip().lower()
    if wide_face in ("down", "up", "flat"):
        return float(w), float(t)
    if wide_face in ("side", "edge"):
        return float(t), float(w)
    raise ValueError("orientation.wide_face must be one of: down/up/flat/side/edge")


def _first_ray_hit_on_polygon_with_edge(
    origin: Point, dir_u: Point, poly: list[Point]
) -> Tuple[Optional[Point], Optional[Tuple[Point, Point]]]:
    """Return (hit_point, hit_edge_segment) for the closest ray hit on polygon boundary."""
    best_t = None
    best_pt: Optional[Point] = None
    best_edge: Optional[Tuple[Point, Point]] = None
    n = len(poly)
    if n < 2:
        return (None, None)
    for i in range(n):
        a = tuple(poly[i])
        b = tuple(poly[(i + 1) % n])
        hit, t, p = ray_segment_intersection(origin, dir_u, a, b)
        if not hit:
            continue
        if t < 1e-9:
            continue
        if best_t is None or t < best_t:
            best_t = t
            best_pt = p
            best_edge = (a, b)
    return (best_pt, best_edge)


def _rect_footprint_from_start_dir_len(start: Point, dir_u: Point, length: float, width_on_floor: float) -> list[Point]:
    ux, uy = dir_u
    sx, sy = start
    ex, ey = (sx + length * ux, sy + length * uy)
    lx, ly = (-uy, ux)  # left
    hw = width_on_floor / 2.0
    p1 = (sx + hw * lx, sy + hw * ly)
    p2 = (sx - hw * lx, sy - hw * ly)
    p3 = (ex - hw * lx, ey - hw * ly)
    p4 = (ex + hw * lx, ey + hw * ly)
    return [p1, p2, p3, p4]


def _clip_polygon_to_edge_halfplane(
    poly: list[Point],
    edge: Tuple[Point, Point],
    keep_point: Point,
    *,
    overlap_eps: float = 0.001,
) -> list[Point]:
    """Clip polygon to the half-plane defined by the infinite line through edge.

    We keep the side containing keep_point. `overlap_eps` shifts the clipping line slightly
    *toward the clipped-away side*, so the kept polygon extends by a tiny amount. This avoids
    visible pixel gaps in OpenSCAD renders due to floating point / rasterization artifacts.
    """
    a, b = edge
    ax, ay = a
    bx, by = b
    sx, sy = (bx - ax, by - ay)

    # Candidate normal (perp to edge)
    nx, ny = (sy, -sx)  # right normal

    # Choose sign so that keep_point is inside (dot((p- a), n) <= 0)
    kx, ky = keep_point
    if (kx - ax) * nx + (ky - ay) * ny > 0:
        nx, ny = (-nx, -ny)

    # Shift the line point slightly against the normal so the kept region "overlaps" by eps.
    nlen = (nx * nx + ny * ny) ** 0.5
    if nlen > 1e-12 and overlap_eps:
        ux, uy = (nx / nlen, ny / nlen)
        ax -= ux * float(overlap_eps)
        ay -= uy * float(overlap_eps)

    return clip_halfplane([tuple(p) for p in poly], (ax, ay), (nx, ny), keep_leq=True)
def _shift_origin_for_reference_edge(
    origin_pt: Point,
    axis_unit: Point,
    ref_edge: str | None,
    params: Dict[str, Any],
    registries: Dict[str, Any] | None,
) -> Point:
    """Shift an origin point that is defined on a specific member edge onto the member centerline.

    Constraints often specify an origin on an edge (e.g., "north" edge 2" south of a face).
    The dim_lumber_member prototype expects placement.start to lie on the member CENTERLINE.
    So we shift by half the member width (in plan) toward the centerline.
    """
    if not ref_edge:
        return origin_pt
    if registries is None:
        # Without registries we cannot know actual member width; keep legacy behavior.
        return origin_pt

    ref = str(ref_edge).strip().lower()
    hw = _member_half_width_on_floor(params, registries)

    # Axis unit (length direction); compute left unit in plan.
    dx, dy = axis_unit
    lx, ly = (-dy, dx)  # left of axis

    if ref in ("left",):
        # origin is on left edge -> move right (negative left) to centerline
        return (origin_pt[0] - lx * hw, origin_pt[1] - ly * hw)
    if ref in ("right",):
        # origin is on right edge -> move left to centerline
        return (origin_pt[0] + lx * hw, origin_pt[1] + ly * hw)

    # Cardinal edges: interpret as global directions (N/S/E/W).
    # origin is on that named edge -> move opposite that direction to centerline.
    dir_map = {
        "n": "N", "north": "N",
        "s": "S", "south": "S",
        "e": "E", "east": "E",
        "w": "W", "west": "W",
        "ne": "NE", "northeast": "NE",
        "nw": "NW", "northwest": "NW",
        "se": "SE", "southeast": "SE",
        "sw": "SW", "southwest": "SW",
    }
    tok = dir_map.get(ref, ref.upper())
    ux, uy = unit_from_dir_token(tok)
    return (origin_pt[0] - ux * hw, origin_pt[1] - uy * hw)



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

    # Default Z placement: for constraint-authored scenes, treat all solid z-bases as
    # relative to the anchor boundary's top surface (wall_height). This makes generated
    # SCAD easier to visually verify in tests (members sit on top of the room boundary).
    anchor_top_z = 0.0
    try:
        anchor_id = scene.get('anchor_id') or scene_constraints.get('anchor_id')
        if anchor_id and anchor_id in obj_index:
            g = (obj_index[anchor_id] or {}).get('geom')
            if isinstance(g, dict) and g.get('kind') == 'boundary':
                anchor_top_z = float(g.get('wall_height', 0.0))
    except Exception:
        anchor_top_z = 0.0

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
            # Lift solids onto the anchor's top surface for visual verification.
            if o.get("prototype") == "poly_extrude" and anchor_top_z != 0.0:
                oo = copy.deepcopy(o)
                p = oo.get("params", {}) or {}
                ex = p.get("extrusion")
                if isinstance(ex, dict):
                    zb = float(ex.get("z_base", 0.0))
                    ex["z_base"] = zb + anchor_top_z
                    p["extrusion"] = ex
                    oo["params"] = p
                concrete_objects.append(oo)
            else:
                concrete_objects.append(o)
            continue

        params = copy.deepcopy(o.get("params", {}))
        pc = params.pop("placement_constraints", None)
        if anchor_top_z != 0.0:
            # If caller did not specify z_base, place member on top of anchor boundary.
            params.setdefault("z_base", anchor_top_z)
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
            # Semantic rule (correct): offset_in is measured from the referenced feature
            # to the NEAREST FACE of the placed member (not the centerline), measured
            # perpendicular to the feature and in the specified dir.
            feature_h = origin["feature"]
            require_handle(feature_h)
            oid, feat = _parse_handle(feature_h)
            seg = resolve_feature_segment(obj_index[oid], feat)
            a, b = seg

            dir_tok = str(origin.get("dir", "S"))
            uDx, uDy = unit_from_dir_token(dir_tok)
            off_face = float(origin.get("offset_in", 0.0))

            # Choose midpoint of the referenced feature as the anchor point.
            mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0

            # Compute the axis unit now, so we can translate a face-based offset into a
            # centerline placement.start (required by dim_lumber_member).
            pos_tok = axis_to_dir_token(axis, positive=True)
            ax, ay = unit_from_dir_token(pos_tok)
            # Member normal in plan (left of axis). Faces are offset ±half_width along this normal.
            nx, ny = (-ay, ax)
            d_dot_n = (uDx * nx + uDy * ny)

            # Place the NEAREST FACE at off_face from the feature along dir.
            face_pt = (mx + uDx * off_face, my + uDy * off_face)

            # Translate from face point to centerline point along dir.
            # If dir isn't perpendicular to the member axis (i.e., no component along the
            # member normal), the "nearest face" is not well-defined.
            if registries is None:
                # Without registries we cannot know actual member width; treat off_face
                # as a centerline offset (legacy-ish fallback).
                origin_pt = face_pt
            else:
                if abs(d_dot_n) < 1e-9:
                    raise ValueError(
                        f"offset_from_feature dir '{dir_tok}' must have a non-zero component perpendicular "
                        f"to axis '{axis}' for dim_lumber_member '{o['id']}'"
                    )
                hw = _member_half_width_on_floor(params, registries)
                # Project half-width onto the measurement direction.
                shift = hw / abs(d_dot_n)
                origin_pt = (face_pt[0] + uDx * shift, face_pt[1] + uDy * shift)

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
        # NOTE: for offset_from_feature we may have computed pos_tok/axis unit above; recompute
        # here for clarity and to avoid accidental reuse across branches.
        pos_tok = axis_to_dir_token(axis, positive=True)
        dx, dy = unit_from_dir_token(pos_tok)
        origin_pt = _shift_origin_for_reference_edge(origin_pt, (dx, dy), ref_edge, params, registries)
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

            # try segment first, then polygon (keeping track of the boundary edge we hit)
            pt: Optional[Point] = None
            hit_edge: Optional[Tuple[Point, Point]] = None
            try:
                seg = resolve_feature_segment(target_obj, ufeat)
                pt = ray_segment_first_hit(origin_pt, udir, seg)
                hit_edge = seg
            except Exception:
                seg = None

            if pt is None:
                poly = resolve_feature_polygon(target_obj, ufeat)
                pt, hit_edge = _first_ray_hit_on_polygon_with_edge(origin_pt, udir, poly)

            if pt is None:
                raise ValueError(f"Ray from '{o['id']}' did not hit '{until_h}'")

            start = origin_pt
            end = pt

            # Optional: clip the member footprint to the hit line so it visually abuts in plan.
            # This is especially important for diagonal members where a centerline ray hit
            # otherwise produces only a single-point touch.
            clip_to_hit_line = bool(extent.get("clip_to_hit_line", True))
            if clip_to_hit_line and hit_edge is not None and registries is not None:
                width_on_floor, height = _member_width_and_height(params, registries)

                vx, vy = (end[0] - start[0], end[1] - start[1])
                base_len = (vx * vx + vy * vy) ** 0.5
                over_len = base_len + width_on_floor * 2.0

                rect = _rect_footprint_from_start_dir_len(start, udir, over_len, width_on_floor)
                clipped = _clip_polygon_to_edge_halfplane(rect, hit_edge, keep_point=start)

                params_poly = {
                    "footprint": [[float(x), float(y)] for (x, y) in clipped],
                    "extrusion": {"z_base": float(params.get("z_base", 0.0)), "height": float(height)},
                }
                new_obj = copy.deepcopy(o)
                new_obj["prototype"] = "poly_extrude"
                new_obj["params"] = params_poly
                concrete_objects.append(new_obj)

                # Make this new geometry available for any subsequent constraints.
                try:
                    new_obj["geom"] = poly_extrude.resolve(params_poly)
                    obj_index[new_obj["id"]] = new_obj
                    support.setdefault("objects", []).append(new_obj)
                    catalog = build_feature_catalog(support)
                    feat_map.update({oo['id']: oo.get('features', []) for oo in catalog.get('objects', [])})
                except Exception:
                    pass
                continue

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