# Nautilus vessel model notes

This directory contains the independent Gazebo description of the Nautilus
catamaran. It does not modify or replace the existing `vessel_v2` model.

## Source audit

The prompt refers to `nautilus_vessell_hull.stl`, but the supplied file is
`nautilus_vessel_hull.stl`; the existing filename was treated as authoritative.
All three binary STL files were verified as readable. Their source dimensions
confirm millimetre units:

| Mesh | Source bounding-box dimensions (mm) |
|---|---:|
| Hull | 2013.45 x 2943.12 x 1450.94 |
| Left propeller | 223.79 x 119.19 x 209.89 |
| Right propeller | 223.79 x 119.19 x 209.89 |

All SDF and URDF mesh elements therefore use a `0.001` scale.

## Frames and geometry

The hull taper and the propellers' positive-CAD-Y placement identify negative
CAD Y as the forward direction. The CAD-to-body transform is consequently:

```text
X_body = -Y_CAD
Y_body =  X_CAD
Z_body =  Z_CAD
```

This is `Rz(+pi/2)` on each visual mesh. The transformed body convention is X
forward, Y port and Z up. Under this rotation the CG becomes `(0.1, 0, -0.05)`
m and the CAD-aligned X/Y inertia moments swap, yielding body-frame moments
`Ixx=187`, `Iyy=88`, `Izz=215` kg m^2. These are the provisional source values;
no stability-oriented CG retuning is applied.

The two collision boxes remain separate and are expressed directly in the body
frame at Y=+/-0.75 m. At the requested 0.18 m draft, their model origin is
0.035 m above the water surface.

## Propeller pivots and unresolved source inconsistencies

The source propeller STLs contain global CAD coordinates. Local copies were
created by subtracting these bounding-box centres in millimetres:

```text
left:  (-827.762909,  850.508575, 134.241518)
right: (-214.704571, 1167.146301, 134.241518)
```

The approximately circular X-Z extents and shorter Y extent identify CAD Y as
the shaft direction, which transforms to the body X joint axis. Recentring
places that shaft through each link origin and prevents orbital motion.

The global mesh centres disagree substantially with the nominal positions in
the input specification, and the nominal CAD-Y sign conflicts with the stern
identified from the geometry. The model therefore uses the physically
consistent body-frame locations `(-1.35, +0.75, -0.12)` m for the left/port
propeller and `(-1.35, -0.75, -0.12)` m for the right/starboard propeller.
These positions should be confirmed against authoritative CAD assembly data.
No propulsion plugin is enabled.

The two propeller meshes appear geometrically equivalent apart from their
source translations; counter-rotating blade handedness could not be confirmed.

## Mass, buoyancy and hydrodynamics

The base link is 259.998 kg and each propeller link is 0.001 kg, keeping total
model mass exactly 260 kg without assigning the full mass to multiple links.
The supplied inertia tensor remains on the base link; the 1 g propeller inertia
is intentionally negligible. The two supplied pontoon boxes are separate
collision volumes on `base_link`, as requested by the source specification.

At 0.18 m immersion, the collision boxes displace 0.3888 m^3, corresponding to
about 398.5 kg of seawater at 1025 kg/m^3. With a 260 kg vehicle, their static
box-based equilibrium immersion is approximately 0.1175 m. Both the supplied
mass and geometry are preserved; the discrepancy is not hidden by retuning.

The supplied signed linear and quadratic damping derivatives are mapped to the
existing Gazebo Harmonic Hydrodynamics system. No added-mass values, buoyancy
system or propulsion system have been added. Buoyancy remains a world-level
integration step for later work.
