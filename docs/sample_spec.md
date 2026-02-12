# Drawing of Sunken Living Room Modification

# Assumptions

## Enumeration and specification of Geometric Objects

Each object is enumerated and named. Sub-features of objects (edges/faces/sections/surfaces) are also named when being referred to. For each object, the **minimum information needed to determine its 3D placement and orientation** is specified; remaining vertices are derived from the implied shape (e.g., joist as a prism from a centerline, width, depth, and elevation). Some points/edges are defined **relative to named features** of previously-defined objects. The construction order is explicit so all references are realizable at the time they are used.  The drawing order of point lists are in the order they are specified.

## Terminology

The project coordinate system is defined in this spec as:

* For any object whose orientation is defined by contact with another object:  
  * the back side of the object is the side facing the reference object.  
  * the front side is the opposite side.  
  * left and right are defined when looking from the front toward the back.  
* Unless otherwise stated references to sides/edges of an object are in plan (2D footprint).  
* “Sits on” means the bottom elevation of the object equals the top elevation of the referenced object.  
* “Against” a wall or face means the corresponding footprint edge lies on the same supporting line as the referenced wall or edge (no offset).

## Geometric Assumptions

* Unless explicitly stated otherwise, all lumber dimensions in this specification refer to **actual (dressed) dimensions**, not nominal sizes.  
* **Unless explicitly stated otherwise, all linear framing members are located and dimensioned by their finished faces (edges), not by their centerlines.**  
* **When framing members are described as “equally spaced”, the spacing refers to clear distance between adjacent member faces, unless explicitly stated otherwise.**  
* **Where a framing member would extend beyond any enclosing wall or boundary, the member shall be trimmed so that its final geometry is the intersection of the member volume and the interior of the enclosing room boundary.**  
* **When a framing member is described as “ending where it intersects” another member or boundary, the member is extended in its specified direction until its footprint would first touch the footprint of the referenced member or boundary. Unless otherwise specified the member is then trimmed at that location so its end face is flush with the contacted face or edge.**  
* **In plan view, \+Y is North, −Y is South, \+X is East, −X is West. Directions like “south-west” mean the 45° direction combining South and West (equal components).**  
*   
* 

## SCAD Generation A SCAD file is to be produced with:

* **Constants**  
  * Numeric parameters from the spec  
  * Boolean toggles to include/exclude each object or group  
* **Geometry functions (data only)**  
  * One function per object that returns the object’s **authoritative geometry as data (**Preferably: a 2D footprint \+ {z\_base, height} **or** explicit 3D points)  
  * Geometry functions may reference other geometry functions when points are defined relative to other objects  
  * No function may depend (directly or indirectly) on itself (no cycles)  
* **Rendering modules (drawing only)**  
  * One module per object that draws the object by calling its geometry function(s)  
  * Modules do not compute dependent geometry; they only render  
* Functions and rendering modules should use the names in this spec

# Geometric Objects

## Octagon 

* A room which is a regular octagon with a span (flat to flat) of 167″ and a vertical depth of 13.75″.  
* The octagon shall be modeled as boundary surfaces (floor and walls only), not as a solid volume.  
* The floor of the sunken living room is the top horizontal face of the octagon’s vertical extent..  
* The inside of the room is the side of each wall that faces the center of the octagon.  
* The octagon defines the **boundary of the sunken floor**.  
* The “sunken floor” is the flat surface whose outline is this octagon.  
* All objects that “sit on the sunken floor” use this surface as their vertical reference.  
* The octagon is also used only to define the named sides (North, North-East, East, …) and vertices.  
* No physical walls are modeled.  
* All points defined in this specification are inside the octagon unless explicitly stated otherwise  
* Sides counting clockwise from 12:00 will be referred to as “walls”.  There is the North Wall, North East Wall, East Wall, South East Wall, South Wall, South West Wall, West Wall and North West Wall.    
* Vertices will be referred to by the wall names and mean the nearest vertex clockwise around the walls of the octagon.  For example the North Vertex means the vertex between the North Wall and the North East Wall.  
* The color will be dark brown.  
* All other objects are referenced directly or indirectly from this octagon  
* The term north, south, east, west, north east, north west, south west and south east when used in the phrasing “x inches west of y” means a point that is x inches from y and along an imaginary line running from point y to to the wall of the same name where the line is perpendicular to that wall

## Masonry Group

### Chimney

A masonry cuboid that is 52” wide,  47” deep and 10 feet high. It sits on the sunken floor and its back is against the North Wall, centered along that wall. Color is white.

### West Wing 

An irregular quadrilateral that sits on the sunken floor is 3.5 feet tall and whose bottom points are:

1. The bottom back left corner of the Chimney  
2. The North West Vertex  
3. A point along the North West Wall that is 27 inches from that vertex  
4. The bottom front left corner of the Chimney

The side between points 1 and 4 is against the left side of the Chimney.  Color is white.

### East Wing 

An irregular quadrilateral that sits on the sunken floor  is 3.5 feet tall and whose bottom points are:

1. The bottom back right corner of the Chimney  
2. The North Vertex  
3. A point along the North East Wall 27 inches from that vertex  
4. The bottom front right corner of the Chimney

The side between points 1 and 4 is against the right side of the Chimney.  Color is white.

### Old Hearth

The old hearth is a surface at the level of the sunken floor defined by these points:

1. A point on the North West Wall that is 47 inches from the North West Vertex  
2. Point 3 of the West Wing  
3. The bottom front left corner of the Chimney  
4. The bottom front right corner of the Chimney  
5. Point 3 of the East Wing  
6. A point along the North East Wall that is 47 inches from theNorth Vertex  
7. A point 7.5” east and 20” south of the bottom front right corner of the Chimney  
8. A point 7.5” west and 20” south of the bottom front left corner of the Chimney

Color is white.

### New Hearth

The new hearth is a masonry cuboid that is 52” wide, 20” deep and 13.5” high.  It sits on the sunken floor.  The back side is against the front side of the Chimney. Color is blue.

## Framing Group

Colors: Joists and Sleepers are tan.  The subfloor is a darker tan and the Finished Floor is a shade darker.

## Main Sleepers

Sleepers are 1 x 2.5 (actual size) boards that sit on the sunken floor with the 2.5 inch side against the floor and are positioned with their length parallel to the South Wall.  They are:

* The Hearth Sleeper is positioned 2 inches south of the front face of the New Hearth and extends to the East Wall and the West Wall  
* The Ledger Sleeper is positioned 0 inches (from edge) north of the South Wall and extends to the South East and South West Walls.  The ends are angled such that they follow and are against their respective walls.  
* The Middle Sleepers are six sleepers between the previous two which are spaced equally.  They extend from the South West Wall or the West Wall to the South East Wall or the East Wall and their ends are cut appropriately so that they are against those walls.

## Wing Sleepers

Wing Sleepers are also 1 x 2.5 (actual size) boards that sit on the sunken floor with the 2.5 inch side against the floor.

* The Right Wing Sleeper’s north side starts at the point on the North East Wall 49” from the North Vertex and extends south west ending where it intersects with the Hearth Sleeper.  
* The Left Wing Sleeper’s north side start at the point on the North West Wall 49” from the North West Vertex and extends south east where it intersects with the Hearth Sleeper.  
* The Right Mid Wing Sleeper’s south side starts at the North East Vertex and extends south west ending where it intersects with the Hearth Sleeper.  
* The Left Mid Wing Sleeper’s south side starts at the West Vertex and extends south east where it intersects with the Hearth Sleeper.  
  