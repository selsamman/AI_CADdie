Specification for Sunken Living Room Project

# Overview

There is an octagonal sunken living room with a multi-section chimney, which includes an insert, at the back end of the octagon with the insert facing into the remaining sunken living room space.  The goal is to raise the floor so it is level with the main floor.  The insert has already been moved up and a new hearth has been built.  There was an existing hearth that spanned the full width of the chimney sections.  The new hearth which is built on top of the old one is smaller and just extends past the fire box (insert) the minimum compliant distance.  A drawing for a site plan is needed that shows the framing and the new floor.

# Geometry

## Octagon (current sunken living room)

* A regular octagon with flats aligned so the back wall is horizontal (a flat, not a vertex). Dimension 167” is flat-to-flat  
* Depth is 13.75” below main floor level

## Fireplace

Three sections.  The center piece is a masonry chimney that is 52” wide and 47” deep. It abuts the back wall of the octagon and is centered.  It rises over 10 feet. There are masonry wings on each side that rise 3 feet from the sunken floor.  Each wing is an irregular quadrilateral with these points:

1. The back corner of the fireplace  
2. The vertex on either end of the back wall of the octagon (right vertex for right wing, left vertex for left wing)  
3. A point 27 inches out from that vertex along the wall adjacent to the back wall (left or right depending on wing)  
4. The front corner of the fireplace (left or right depending on wing)

The new masonry hearth is in front of the chimney and is 52 wide and 20” deep and is at the level of the main floor.  The old masonry hearth is the fireplace and wings footprint offset outward toward the room by 20”, clipped to octagon.  It is 3/4 below the lower floor level because floor boards are not sitting on top of it. The new hearth sits on top of this in the center.

Important constraints: all framing and subfloor defined later must at least 2 inches from these masonry structures.

## Framing

* The base is 5/4” x 3” sleepers run parallel to the back wall of the Octagon.  Here is the layout:  
  * First sleeper is placed parallel to the front wall with its **front edge coincident with the inside face of the front wall**..    
  * Second sleeper two inches in front of the hearth and parallel to the front of the hearth(will be referred to as hearth sleeper).   
  * Fill in four evenly spaced sleepers between those two that run parallel to the other two.   
  * There are two more sleepers that go in between the sleeper in front of the hearth and the wings.   The first one runs parallel to the old hearth in front of the wing from the wall adjacent the back to connect with the sleeper in front of the hearth.  The edge closest to the masonry is two inches from the masonry.  The midpoint of the other sleeper is located at the vertex at the junction of the side wall and the wall adjacent to the back wall. It runs parallel to the aforementioned sleeper into the sleeper in front of the wall.  The ends are cut at required angles fit against the wall and the other sleeper it joins.  
* 2x12 ledger beams around the walls running up to two inches shy of the masonry.  
* Perpendicular 2x12 joists. Specifically:  
  * Two joists are placed such that their edges nearest the masonry are two inches out from the sides of the hearth (will be referred to as hearth joists).  
  * Between each hearth joist and the perimeter ledger on that same side place two more joists evenly spaced.  
  * This should make joist spacing roughly 15 \- 19 inches  
  * The lengths of the joists are such that they accommodate the perimeter ledger  next to the masonry which is defined next   
* The final segments to complete a continuous perimeter ring are three 2x12 beams attaching to the masonry end of the ledger.  The center one attaches to the end of the hearth joists and the two joists in between the hearth joists.  It runs parallel to the hearth two inches from the front of the hearth.   The two wing segments are parallel to the front of the wings and two inches from the front of the wing.  They run from each of the hearth joists out to the end of the perimeter ledger beam on the wall adjacent the back wall and also connect to the two joists inbetween. The result is a continuous ledger around the perimeter that is two inches shy of the chimney, wings and hearth.  
* On each side of the hearth, the hearth joist and the two joists between that hearth joist and the perimeter ledger extend over the old hearth. They must be notched on the bottom such that their bottom edge is 2 inches from the surface of the old hearth.  The old hearth is .75 below lower floor level.  Since the sleeper lifts the joist an inch, .25 inches needs to be cut off the bottom of the joist that is over the hearth in order to keep the bottom of the joist two inches from the surface of the old hearth.  
* 2x12 midspan blocking is required.  
* T\&G plywood filling the entire area but leaving a two inch perimeter around the hearth and wings.  
* The long dimension of each plywood sheet must be run parallel with the joists to comply with code. Plywood spans can be optimized for minimum material use without regard for seams falling on joists or blocks. 

  N.B. All “2 inches from masonry” constraints are measured from the joist or edge (not centerline) closest to the masonry." To resolve any conflicts in algorithmic specification of spacing please resolve in this order:  
1. satisfy all 2" clearances,  
2. then keep O.C. spacing as close as possible,  
3. if mismatch, distribute error evenly except fixed joists near hearth.

## Flooring

On top of the plywood subfloor will be 2.5 inch unfinished T\&G floor boards .75 high. There are two patterns.  The boards near the chimney run parallel to the joists and the rest run perpendicular to the joists.  The demarcation line connects the two vertices that bound the **front flat wall** (opposite the chimney). The boards running towards the hearth and wings will stick out over the plywood and lie on the steel angle support.The steel angle is fastened to the masonry-side perimeter ring beams described in the framing section. Since it is only 1.5” a half inch span of the floor boards  is unsupported

# Drawing Guidance

* Drawing will be scad file compatible with openscad  
* Use a coordinate scheme where the origin is at octagon center; \+Y toward chimney; units inches; Z=0 at sunken floor; Z=13.75 at main floor  
* Make each object set a module and include a boolean at the top to include/exclude it  
* Make everything a tan wood color  
* The fireplace in white  
* The new hearth in blue  
* The old hearth in red brick  
* When drawing floors and subfloors we want to see the individual pieces which would otherwise be blended by openscad.  So make the pieces a tiny bit shorter and add a gap around them so they will show up.  Make the gap a variable and use it in the positioning computation so that the ultimate widths and lengths are preserved over multiple spans of the boards