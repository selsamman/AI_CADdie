import math

def resolve(params: dict) -> dict:
    span = float(params["span_flat_to_flat_in"])
    origin = params["origin"]
    nwn = params["north_wall_normal"]

    nx, ny = float(nwn[0]), float(nwn[1])
    L = math.hypot(nx, ny)
    if L == 0:
        raise ValueError("north_wall_normal cannot be zero vector")
    nx, ny = nx/L, ny/L

    a = span / 2.0
    s = 2*a*math.tan(math.pi/8.0)
    c = a*math.tan(math.pi/8.0)  # retained for clarity

    verts_local = [
        (-s/2,  a),
        ( s/2,  a),
        ( a,  s/2),
        ( a, -s/2),
        ( s/2, -a),
        (-s/2, -a),
        (-a, -s/2),
        (-a,  s/2),
    ]

    # rotate local +Y to provided normal (nx, ny)
    theta = math.atan2(nx, ny)
    ct, st = math.cos(theta), math.sin(theta)

    ox, oy = float(origin[0]), float(origin[1])

    def rot(x, y):
        xr = x*ct - y*st
        yr = x*st + y*ct
        return [xr + ox, yr + oy]

    fp = [rot(x, y) for (x, y) in verts_local]
    wall_h = float(params.get("wall_height_in", 1.0))
    return {"kind": "boundary", "footprint": fp, "wall_height": wall_h}
