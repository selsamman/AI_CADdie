from copy import deepcopy
from engine.prototypes import poly_extrude, regular_octagon_boundary
from engine.geom import clip_convex

def _resolve_object(obj):
    proto = obj["prototype"]
    params = obj.get("params", {})
    if proto == "poly_extrude":
        geom = poly_extrude.resolve(params)
    elif proto == "regular_octagon_boundary":
        geom = regular_octagon_boundary.resolve(params)
    else:
        raise ValueError(f"Unknown prototype: {proto}")
    out = deepcopy(obj)
    out["geom"] = geom
    return out

def build_scene(scene: dict, registries: dict) -> dict:
    # Resolve prototypes into explicit geometry
    objects = {o["id"]: _resolve_object(o) for o in scene.get("objects", [])}

    # Execute operators on resolved geometry (v0.2 supports clip_to_object for convex clippers)
    for op in scene.get("operators", []):
        if op.get("op") != "clip_to_object":
            raise ValueError(f"Unknown operator: {op.get('op')}")
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
                # Only solids are clipped in v0.2
                continue
            subj = tgeom.get("footprint", [])
            clipped = clip_convex([(float(x),float(y)) for x,y in subj],
                                  [(float(x),float(y)) for x,y in clip_fp])
            tgeom["footprint"] = [[p[0], p[1]] for p in clipped]

    return {"anchor_id": scene["anchor_id"], "objects": objects}
