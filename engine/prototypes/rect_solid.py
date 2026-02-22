from __future__ import annotations

"""rect_solid prototype resolver.

Creates a simple rectangular prism in plan space.

Footprint vertex order contract (required by engine/features.py):

  [0] back-left
  [1] back-right
  [2] front-right
  [3] front-left

Where:
  - "back" is the face whose outward normal matches back_normal.
  - "left"/"right" are defined looking from front toward back.

NOTE: Do not change this ordering without updating feature resolution logic.
"""

from typing import Any, Dict, List, Tuple
import math


def _unit(v: List[float] | Tuple[float, float]) -> Tuple[float, float]:
    x, y = float(v[0]), float(v[1])
    L = math.hypot(x, y)
    if L == 0:
        raise ValueError("back_normal cannot be zero vector")
    return (x / L, y / L)


def resolve(params: Dict[str, Any], registries: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Resolve params into a solid with a rectangular footprint.

    Params:
      - width_in (float)
      - depth_in (float)
      - origin ([x,y]) center of the BACK face in plan
      - back_normal ([nx,ny]) unit-ish vector pointing from interior toward the back wall (default [0,1])
      - height_in (float)
      - z_base (float, optional, default 0.0)
    """

    width = float(params["width_in"])
    depth = float(params["depth_in"])
    height = float(params["height_in"])
    if width <= 0 or depth <= 0 or height <= 0:
        raise ValueError("width_in, depth_in, and height_in must be > 0")

    origin = params["origin"]
    if not (isinstance(origin, list) and len(origin) == 2):
        raise ValueError("origin must be [x,y]")
    ox, oy = float(origin[0]), float(origin[1])

    back_normal = params.get("back_normal", [0, 1])
    if not (isinstance(back_normal, list) and len(back_normal) == 2):
        raise ValueError("back_normal must be [nx,ny]")
    bx, by = _unit(back_normal)

    # "Front" points toward the interior, opposite back_normal.
    fx, fy = (-bx, -by)

    # Define left/right looking from front toward back (looking along +back_normal).
    # For back_normal = [0,1] (North), right is +X (East).
    rx, ry = (by, -bx)        # right
    lx, ly = (-by, bx)        # left

    hw = width / 2.0

    # Back face center is origin.
    back_left = (ox + hw * lx, oy + hw * ly)
    back_right = (ox + hw * rx, oy + hw * ry)
    front_right = (back_right[0] + depth * fx, back_right[1] + depth * fy)
    front_left = (back_left[0] + depth * fx, back_left[1] + depth * fy)

    footprint = [
        [back_left[0], back_left[1]],
        [back_right[0], back_right[1]],
        [front_right[0], front_right[1]],
        [front_left[0], front_left[1]],
    ]

    z_base = float(params.get("z_base", 0.0))

    return {
        "kind": "solid",
        "footprint": footprint,
        "extrusion": {"z_base": z_base, "height": height},
    }
