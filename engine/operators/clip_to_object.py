from __future__ import annotations

from typing import Any, Dict

from engine.geom import clip_convex


def apply(
    objects: Dict[str, Dict[str, Any]],
    templates: Dict[str, Dict[str, Any]],
    op: Dict[str, Any],
    resolve_fn,
) -> Dict[str, Dict[str, Any]]:
    """Clip target solid footprints by the clip object's footprint.

    Signature matches the operator registry contract.
    """
    clip_id = op["clip_object_id"]
    target_ids = op.get("target_ids", [])
    if clip_id not in objects:
        raise ValueError(f"clip_object_id not found: {clip_id}")

    clip_geom = objects[clip_id]["geom"]
    if clip_geom.get("kind") not in ("boundary", "solid"):
        raise ValueError("clip_to_object expects clip object to have footprint geometry")
    clip_fp = clip_geom.get("footprint")
    if not clip_fp:
        return objects

    for tid in target_ids:
        if tid not in objects:
            raise ValueError(f"target_id not found: {tid}")
        tgeom = objects[tid]["geom"]
        if tgeom.get("kind") != "solid":
            # Only solids are clipped
            continue
        subj = tgeom.get("footprint", [])
        clipped = clip_convex(
            [(float(x), float(y)) for x, y in subj],
            [(float(x), float(y)) for x, y in clip_fp],
        )
        tgeom["footprint"] = [[p[0], p[1]] for p in clipped]

    return objects
