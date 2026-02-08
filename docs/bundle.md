# DescriptiveCAD Bundle v0.1
BUNDLE_ID: descriptivecad:v0.1

## Hard rules
1) Do not guess missing numeric inputs. Ask questions and propose a spec patch.
2) Coordinate system: X=east, Y=north, Z=up. Pit floor Z=0.
3) Output is either:
   - `NO_AMBIGUITIES` + `scene.json`, or
   - `AMBIGUITIES_FOUND` + questions + spec patch (no scene.json).

## v0.1 operators
- distribute_linear_array: place N members with equal spacing (center_to_center or clear_gap)
- clip_by_halfplane: trim a footprint polygon by a half-plane
