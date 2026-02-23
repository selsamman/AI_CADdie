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


def _resolve_profile_entry(params: Dict[str, Any], registries: Dict[str, Any] | None) -> Dict[str, Any] | None:
    """Return the resolved registry profile entry dict if one applies.

    If the profile is provided as an explicit actual size, there is no registry
    entry to consult and this returns None.
    """
    profile = params.get("profile", {})
    if "actual" in profile:
        return None

    pid = profile.get("id")
    if not pid:
        system = profile.get("system", "S4S")
        nominal = profile.get("nominal")
        if nominal:
            pid = f"{system}:{nominal}"
    if not pid:
        return None

    if not registries:
        return None
    table = registries.get("lumber_profiles", {})
    # Backwards-compatible shorthand: allow id like "2x6" and interpret as "S4S:2x6"
    if pid not in table and ":" not in pid:
        alt = f"S4S:{pid}"
        if alt in table:
            pid = alt

    entry = table.get(pid)
    return entry if isinstance(entry, dict) else None

def resolve(params: Dict[str, Any], registries: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Resolve a dimensional lumber member into a solid footprint extrusion.

    Convention (v0.2):
    - placement.start is the CENTER of the start/end face in plan view.
    - placement.direction gives the axis along the member length.
    - placement.length is the member length in inches.
    - orientation.wide_face can be 'down'/'up'/'flat' or 'side'/'edge'.
      Priority for wide_face:
        1) params.orientation.wide_face if explicitly set
        2) registry profile default_orientation.wide_face if present
        3) fallback to 'down'
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
    if isinstance(orient, dict) and "wide_face" in orient:
        wide_face = str(orient.get("wide_face")).strip().lower()
    else:
        entry = _resolve_profile_entry(params, registries)
        default_wide_face = None
        if entry:
            default_orientation = entry.get("default_orientation")
            if isinstance(default_orientation, dict):
                default_wide_face = default_orientation.get("wide_face")
        wide_face = str(default_wide_face if default_wide_face is not None else "down").strip().lower()

    if wide_face in ("down", "up", "flat"):
        height = t
        width_on_floor = w
    elif wide_face in ("side", "edge"):
        height = w
        width_on_floor = t
    else:
        raise ValueError("orientation.wide_face must be one of: down/up/flat/side/edge")

    z_base = float(params.get("z_base", 0.0))

    # Construct footprint (CCW) as rectangle with one end centered at start.
    # Start end center at (sx,sy); end center at (sx,sy) + length*u
    ex, ey = sx + length*ux, sy + length*uy

    # Perpendicular (left) unit vector
    vx, vy = -uy, ux
    hw = width_on_floor / 2.0

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
