from copy import deepcopy
from engine.prototypes import poly_extrude, regular_octagon_boundary, dim_lumber_member
from engine.geom import clip_convex, clip_halfplane, first_ray_polygon_hit, dot

def _unit(vx: float, vy: float):
    mag = (vx*vx + vy*vy) ** 0.5
    if mag == 0:
        raise ValueError("Zero-length direction vector")
    return vx/mag, vy/mag

def _resolve_object(obj, registries):
    proto = obj["prototype"]
    params = obj.get("params", {})
    if proto == "poly_extrude":
        geom = poly_extrude.resolve(params)
    elif proto == "regular_octagon_boundary":
        geom = regular_octagon_boundary.resolve(params)
    elif proto == "dim_lumber_member":
        geom = dim_lumber_member.resolve(params, registries)
    else:
        raise ValueError(f"Unknown prototype: {proto}")
    out = deepcopy(obj)
    out["geom"] = geom
    return out

def build_scene(scene: dict, registries: dict) -> dict:
    # Split objects into concrete objects vs operator-generated templates.
    templates = {o["id"]: deepcopy(o) for o in scene.get("objects", []) if str(o.get("role","")).lower() == "template"}
    concrete_list = [o for o in scene.get("objects", []) if str(o.get("role","")).lower() != "template"]

    # Resolve prototypes into explicit geometry (concrete objects only)
    objects = {o["id"]: _resolve_object(o, registries) for o in concrete_list}

    # Execute operators on resolved geometry
    for op in scene.get("operators", []):
        if op.get("op") == "distribute_evenly_between":
            template_id = op["template_object_id"]
            between = op["between_object_ids"]
            count = int(op["count"])
            id_prefix = op.get("id_prefix", f"{template_id}_")
            if template_id not in templates:
                raise ValueError(f"template_object_id not found (role=template): {template_id}")
            if not (isinstance(between, list) and len(between) == 2):
                raise ValueError("between_object_ids must be [id_a, id_b]")
            a_id, b_id = between[0], between[1]
            if a_id not in objects or b_id not in objects:
                raise ValueError("between_object_ids must reference concrete objects already in scene")

            # Anchor points: prefer placement.start from source params, else centroid of footprint.
            def _anchor_pt(obj):
                params = obj.get("params", {})
                plc = params.get("placement", {})
                start = plc.get("start")
                if isinstance(start, list) and len(start) == 2:
                    return float(start[0]), float(start[1])
                fp = obj.get("geom", {}).get("footprint") or []
                if fp:
                    xs = [p[0] for p in fp]; ys = [p[1] for p in fp]
                    return sum(xs)/len(xs), sum(ys)/len(ys)
                raise ValueError("Cannot determine anchor point for distribute_evenly_between")

            ax, ay = _anchor_pt(objects[a_id])
            bx, by = _anchor_pt(objects[b_id])

            # Generate count objects at equally spaced points between A and B (excluding endpoints).
            for i in range(1, count+1):
                t = i / (count + 1.0)
                sx = ax + (bx - ax) * t
                sy = ay + (by - ay) * t

                inst = deepcopy(templates[template_id])
                inst.pop("role", None)
                inst["id"] = f"{id_prefix}{i}"
                inst.setdefault("params", {})
                inst["params"].setdefault("placement", {})

                # placement.start may be omitted in template; it is provided by this operator.
                inst["params"]["placement"]["start"] = [sx, sy]

                # Resolve and insert
                objects[inst["id"]] = _resolve_object(inst, registries)
            continue

        if op.get("op") == "clip_to_object":
            clip_id = op["clip_object_id"]
            target_ids = op.get("target_ids", [])
            if clip_id not in objects:
                raise ValueError(f"clip_object_id not found: {clip_id}")
            clip_geom = objects[clip_id]["geom"]
            if clip_geom.get("kind") not in ("boundary","solid"):
                raise ValueError("clip_to_object expects clip object to have footprint geometry")
            clip_fp = clip_geom.get("footprint")
            if not clip_fp:
                continue

            for tid in target_ids:
                if tid not in objects:
                    raise ValueError(f"target_id not found: {tid}")
                tgeom = objects[tid]["geom"]
                if tgeom.get("kind") != "solid":
                    # Only solids are clipped
                    continue
                subj = tgeom.get("footprint", [])
                clipped = clip_convex([(float(x),float(y)) for x,y in subj],
                                      [(float(x),float(y)) for x,y in clip_fp])
                tgeom["footprint"] = [[p[0], p[1]] for p in clipped]

        elif op.get("op") == "extend_and_trim_to_object":
            src_id = op["source_object_id"]
            tgt_id = op["target_object_id"]
            edge = op["source_edge"]  # [i, j] indices into footprint
            direction = op["direction"]  # [dx, dy]

            if src_id not in objects:
                raise ValueError(f"source_object_id not found: {src_id}")
            if tgt_id not in objects:
                raise ValueError(f"target_object_id not found: {tgt_id}")

            sgeom = objects[src_id]["geom"]
            tgeom = objects[tgt_id]["geom"]
            if sgeom.get("kind") != "solid":
                raise ValueError("extend_and_trim_to_object expects source kind=solid")
            if tgeom.get("kind") not in ("solid", "boundary"):
                raise ValueError("extend_and_trim_to_object expects target to have a footprint")

            sfp = [(float(x), float(y)) for x, y in sgeom.get("footprint", [])]
            tfp = [(float(x), float(y)) for x, y in tgeom.get("footprint", [])]
            if len(sfp) < 3 or len(tfp) < 3:
                continue

            i, j = int(edge[0]), int(edge[1])
            if i < 0 or j < 0 or i >= len(sfp) or j >= len(sfp):
                raise ValueError("source_edge indices out of range")

            ex1, ey1 = sfp[i]
            ex2, ey2 = sfp[j]
            mx, my = (ex1 + ex2) / 2.0, (ey1 + ey2) / 2.0

            dx, dy = float(direction[0]), float(direction[1])
            udx, udy = _unit(dx, dy)

            hit, t_hit, p_hit = first_ray_polygon_hit((mx, my), (udx, udy), tfp)
            if not hit:
                continue

            # Trim: keep the half-plane behind the contact point.
            # NOTE: This v0.2 implementation does not attempt to *extend* a member if it is too short.
            trimmed = clip_halfplane(sfp, p_hit, (udx, udy), keep_leq=True)
            sgeom["footprint"] = [[p[0], p[1]] for p in trimmed]

        else:
            raise ValueError(f"Unknown operator: {op.get('op')}")

    return {"anchor_id": scene["anchor_id"], "objects": objects}
