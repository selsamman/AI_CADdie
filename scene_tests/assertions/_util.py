from __future__ import annotations

import math
from typing import Iterable


def assert_almost_equal(a: float, b: float, tol: float = 1e-6, msg: str | None = None) -> None:
    if abs(a - b) > tol:
        raise AssertionError(msg or f"Expected {a} ≈ {b} (tol={tol})")


def side_lengths(footprint: list[list[float]]) -> list[float]:
    if len(footprint) < 2:
        return []
    pts = [(float(x), float(y)) for x, y in footprint]
    out: list[float] = []
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        out.append(math.hypot(x2 - x1, y2 - y1))
    return out


def assert_has_object(resolved_scene: dict, obj_id: str) -> dict:
    objs = resolved_scene.get("objects") or {}
    if obj_id not in objs:
        raise AssertionError(f"Expected object id '{obj_id}' in resolved scene")
    return objs[obj_id]
