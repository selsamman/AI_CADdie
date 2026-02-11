def resolve(params: dict) -> dict:
    fp = params["footprint"]
    ex = params["extrusion"]
    return {"kind": "solid", "footprint": fp, "extrusion": {"z_base": ex["z_base"], "height": ex["height"]}}
