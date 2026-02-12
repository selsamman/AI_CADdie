from __future__ import annotations
from typing import Dict, Any, Tuple, List
import math

def _unit_from_direction(d: str) -> Tuple[float, float]:
    d = d.strip().lower().replace("_","").replace("-","")
    dirs = {
        "e": (1.0, 0.0), "east": (1.0, 0.0),
        "w": (-1.0, 0.0), "west": (-1.0, 0.0),
        "n": (0.0, 1.0), "north": (0.0, 1.0),
        "s": (0.0, -1.0), "south": (0.0, -1.0),
        "ne": (math.sqrt(0.5), math.sqrt(0.5)), "northeast": (math.sqrt(0.5), math.sqrt(0.5)),
        "nw": (-math.sqrt(0.5), math.sqrt(0.5)), "northwest": (-math.sqrt(0.5), math.sqrt(0.5)),
        "se": (math.sqrt(0.5), -math.sqrt(0.5)), "southeast": (math.sqrt(0.5), -math.sqrt(0.5)),
        "sw": (-math.sqrt(0.5), -math.sqrt(0.5)), "southwest": (-math.sqrt(0.5), -math.sqrt(0.5)),
    }
    if d not in dirs:
        raise ValueError(f"Unsupported direction: {d}")
    return dirs[d]

def _resolve_profile(params: Dict[str, Any], registries: Dict[str, Any] | None) -> Tuple[float, float]:
    profile = params.get("profile", {})
    if "actual" in profile:
        a = profile["actual"]
        if not (isinstance(a, list) and len(a) == 2):
            raise ValueError("profile.actual must be [thickness, width] (inches)")
        return float(a[0]), float(a[1])

    # Nominal form: {system:'S4S', nominal:'5/4x2x3'} or just id
    pid = profile.get("id")
    if not pid:
        system = profile.get("system", "S4S")
        nominal = profile.get("nominal")
        if nominal:
            pid = f"{system}:{nominal}"
    if not pid:
        raise ValueError("dim_lumber_member requires profile.actual or profile.id or profile.nominal")

    if not registries:
        raise ValueError("Registries required to resolve profile.id/nominal")
    table = registries.get("lumber_profiles", {})
    # Backwards-compatible shorthand: allow id like "2x6" and interpret as "S4S:2x6"
    if pid not in table and ":" not in pid:
        alt = f"S4S:{pid}"
        if alt in table:
            pid = alt

    if pid not in table:
        raise ValueError(f"Unknown lumber profile id: {pid}")
    actual = table[pid].get("actual")
    if not (isinstance(actual, list) and len(actual) == 2):
        raise ValueError(f"Invalid registry entry for {pid}: expected actual=[t,w]")
    return float(actual[0]), float(actual[1])

def resolve(params: Dict[str, Any], registries: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Resolve a dimensional lumber member into a solid footprint extrusion.

    Convention (v0.2):
    - placement.start is the CENTER of the start/end face in plan view.
    - placement.direction gives the axis along the member length.
    - placement.length is the member length in inches.
    - orientation.wide_face can be 'down' (default) or 'up'; if 'down', height=thickness.
      If wide_face == 'down', footprint width = width. If wide_face == 'side', footprint width = thickness.
    """
    t, w = _resolve_profile(params, registries)

    placement = params.get("placement", {})
    start = placement.get("start")
    if not (isinstance(start, list) and len(start) == 2):
        raise ValueError("placement.start must be [x,y]")
    sx, sy = float(start[0]), float(start[1])

    direction = placement.get("direction", "east")
    ux, uy = _unit_from_direction(direction)

    length = float(placement.get("length", 0))
    if length <= 0:
        raise ValueError("placement.length must be > 0")

    orient = params.get("orientation", {})
    wide_face = str(orient.get("wide_face", "down")).strip().lower()

    if wide_face in ("down", "up", "flat"):
        height = t
        width_on_floor = w
    elif wide_face in ("side", "edge"):
        height = w
        width_on_floor = t
    else:
        raise ValueError("orientation.wide_face must be one of: down/up/flat/side/edge")

    z_base = float(params.get("z_base", 0.0))

    # The input start point is normally the CENTER of the start end-face.
    # However, some specs refer to a specific SIDE/EDGE of the board footprint
    # (e.g. "the north side of the sleeper starts at ...").
    #
    # In that case, placement.reference_edge indicates which edge the provided
    # placement.start lies on. We then convert it to the centerline start by
    # shifting by half the footprint width.
    reference_edge = str(placement.get("reference_edge", "centerline")).strip().lower()

    # Perpendicular (left) unit vector
    vx, vy = -uy, ux
    hw = width_on_floor / 2.0

    def _adjust_start_for_reference_edge(sx: float, sy: float) -> Tuple[float, float]:
        if reference_edge in ("center", "centerline", "mid", "middle", ""):
            return sx, sy

        # Shorthand for edges relative to the direction of travel
        if reference_edge in ("left", "right"):
            sgn = 1.0 if reference_edge == "left" else -1.0
            return sx - sgn * hw * vx, sy - sgn * hw * vy

        # Cardinal edges: interpret as the edge that is most extreme in that
        # global direction (N/S/E/W) for this member orientation.
        card = {
            "north": (0.0, 1.0), "n": (0.0, 1.0),
            "south": (0.0, -1.0), "s": (0.0, -1.0),
            "east": (1.0, 0.0), "e": (1.0, 0.0),
            "west": (-1.0, 0.0), "w": (-1.0, 0.0),
        }
        if reference_edge not in card:
            raise ValueError(
                "placement.reference_edge must be one of: centerline, left, right, north, south, east, west"
            )

        gx, gy = card[reference_edge]
        dot = vx * gx + vy * gy
        # If dot > 0, the + (left) edge lies more in the desired global direction.
        # If dot < 0, the - (right) edge lies more in the desired global direction.
        sgn = 1.0 if dot >= 0 else -1.0
        return sx - sgn * hw * vx, sy - sgn * hw * vy

    sx, sy = _adjust_start_for_reference_edge(sx, sy)

    # Construct footprint (CCW) as rectangle with one end centered at start.
    # Start end center at (sx,sy); end center at (sx,sy) + length*u
    ex, ey = sx + length*ux, sy + length*uy

    # Construct footprint (CCW) as rectangle with one end centered at start.
    # Start end center at (sx,sy); end center at (sx,sy) + length*u
    ex, ey = sx + length*ux, sy + length*uy

    p1 = (sx + hw*vx, sy + hw*vy)
    p2 = (sx - hw*vx, sy - hw*vy)
    p3 = (ex - hw*vx, ey - hw*vy)
    p4 = (ex + hw*vx, ey + hw*vy)

    footprint = [[p1[0], p1[1]], [p2[0], p2[1]], [p3[0], p3[1]], [p4[0], p4[1]]]

    return {
        "kind": "solid",
        "footprint": footprint,
        "extrusion": {"z_base": z_base, "height": height},
        "features": {
            "edges": {
                "start": {"type": "segment", "a": [p1[0], p1[1]], "b": [p2[0], p2[1]]},
                "end":   {"type": "segment", "a": [p4[0], p4[1]], "b": [p3[0], p3[1]]},
                "left":  {"type": "segment", "a": [p1[0], p1[1]], "b": [p4[0], p4[1]]},
                "right": {"type": "segment", "a": [p2[0], p2[1]], "b": [p3[0], p3[1]]},
            },
            "faces": {
                "bottom": {"type": "plane", "z": z_base},
                "top": {"type": "plane", "z": z_base + height},
            }
        }
    }
