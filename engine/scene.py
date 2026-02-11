from copy import deepcopy
from engine.prototypes import poly_extrude, regular_octagon_boundary

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
    objects = {o["id"]: _resolve_object(o) for o in scene.get("objects", [])}
    # Placeholder operator execution
    for op in scene.get("operators", []):
        if op.get("op") == "clip_to_object":
            # TODO(v0.3): implement true polygon clipping
            continue
        raise ValueError(f"Unknown operator: {op.get('op')}")
    return {"anchor_id": scene["anchor_id"], "objects": objects}
