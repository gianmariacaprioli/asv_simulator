# Nautilus vessel model

The SDF and URDF use X forward, Y port and Z up. The assembled STL uses
millimetres. Both descriptions scale it by 0.001, rotate it by 1.094045 rad
about Z to align the motor shafts with the longitudinal axis, and offset it
by (-0.404, 0, -0.470) m. The longitudinal offset centers the hull and the
vertical offset aligns the hull bottom with the collision-box keels.

The assembled STL contains both motor housings. The separate propeller
meshes attach to the two rotating links at the estimated aft shaft exits,
(-1.530, +/-0.345, -0.3355) m in the body frame. Each mesh is rotated by
90 degrees about Z to align its CAD shaft axis with the joint's X axis.

## Flotation

The model mass is 260 kg. The base-link center of mass is (0.1, 0, -0.05) m
and its inertia tensor is specified in the SDF and URDF. The two rows of
collision boxes approximate the displacement volume. Each row is divided
into forward and aft sections, with the overall volume centered at the
longitudinal center of mass. The sections provide restoring pitch when
Gazebo 8.15 computes the submerged volume using the local Z axis of each
collision shape.

The total collision volume and the waterplane area correspond to two boxes
of 2.70 x 0.40 x 0.43 m. At 260 kg in 1025 kg/m³ seawater, the estimated
equilibrium draft is about 0.117 m. The default spawn height is 0.098 m
above the water plane. This is the equilibrium of the box approximation.
