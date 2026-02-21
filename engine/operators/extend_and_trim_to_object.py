from __future__ import annotations

from typing import Any, Dict, Tuple

from engine.geom import clip_halfplane, first_ray_polygon_hit


def _unit(vx: float, vy: float) -> Tuple[float, float]:
    mag = (vx * vx + vy * vy) ** 0.5
    if mag == 0:
        raise ValueError("Zero-length direction vector")
    return vx / mag, vy / mag


def apply(
    objects: Dict[str, Dict[str, Any]],
    templates: Dict[str, Dict[str, Any]],
    op: Dict[str, Any],
    resolve_fn,
) -> Dict[str, Dict[str, Any]]:
    """Trim a source solid footprint by raycasting toward a target footprint.

    This v0.2 implementation trims only (it does not extend).
    Signature matches the operator registry contract.
    """
    src_id = op["source_object_id"]
    tgt_id = op["target_object_id"]
    edge = op["source_edge"]  # [i, j]
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
        return objects

    i, j = int(edge[0]), int(edge[1])
    if i < 0 or j < 0 or i >= len(sfp) or j >= len(sfp):
        raise ValueError("source_edge indices out of range")

    ex1, ey1 = sfp[i]
    ex2, ey2 = sfp[j]
    mx, my = (ex1 + ex2) / 2.0, (ey1 + ey2) / 2.0

    dx, dy = float(direction[0]), float(direction[1])
    udx, udy = _unit(dx, dy)

    hit, _t_hit, p_hit = first_ray_polygon_hit((mx, my), (udx, udy), tfp)
    if not hit:
        return objects

    trimmed = clip_halfplane(sfp, p_hit, (udx, udy), keep_leq=True)
    sgeom["footprint"] = [[p[0], p[1]] for p in trimmed]
    return objects
