from __future__ import annotations
from copy import deepcopy
from typing import Any, Dict, Tuple

def apply(objects: Dict[str, Dict[str, Any]], templates: Dict[str, Dict[str, Any]], op: Dict[str, Any], resolve_fn) -> Dict[str, Dict[str, Any]]:
    """Apply distribute_evenly_between to the objects map.

    This module isn't currently used by the bootstrap runner (engine.scene has an inlined implementation),
    but it exists to match the registry contract and enable future refactors.
    """
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

    def _anchor_pt(obj) -> Tuple[float,float]:
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

    for i in range(1, count+1):
        t = i / (count + 1.0)
        sx = ax + (bx - ax) * t
        sy = ay + (by - ay) * t

        inst = deepcopy(templates[template_id])
        inst.pop("role", None)
        inst["id"] = f"{id_prefix}{i}"
        inst.setdefault("params", {})
        inst["params"].setdefault("placement", {})
        inst["params"]["placement"]["start"] = [sx, sy]
        objects[inst["id"]] = resolve_fn(inst)

    return objects
