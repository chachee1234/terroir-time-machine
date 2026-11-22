"""Point-in-plate tests on the sphere for the plate-model polygons (G3c2a1).

A point is tested against a plate polygon by summing the signed angles that each edge subtends
as seen from the point. The sum is about ±2π when the point lies inside the polygon and about 0
when it lies outside. Plate polygons in muller2019.json are small regions (under a hemisphere in
the cases the viewer needs), so this sign test is unambiguous for them.

Plate motion: the plate's rotation quaternion at an age (w, x, y, z) carries a present-day point to
its position at that age. To ask which plate covers a point at an age, undo that rotation (the
conjugate of a unit quaternion) and test the present-day polygon.
"""
import math


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def unit(v):
    m = math.sqrt(_dot(v, v))
    if m == 0:
        raise ValueError("zero vector")
    return (v[0] / m, v[1] / m, v[2] / m)


def lonlat_to_xyz(lat_deg, lon_deg):
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return (math.cos(la) * math.cos(lo), math.cos(la) * math.sin(lo), math.sin(la))


def rotate(q, v):
    """Apply the unit quaternion q = (w, x, y, z) to the vector v (the same maths as pmRot in the viewer)."""
    w, a, b, c = q
    x, y, z = v
    tx = 2 * (b * z - c * y)
    ty = 2 * (c * x - a * z)
    tz = 2 * (a * y - b * x)
    return (x + w * tx + (b * tz - c * ty), y + w * ty + (c * tx - a * tz), z + w * tz + (a * ty - b * tx))


def unrotate(q, v):
    """Undo the rotation q: its conjugate is its inverse for a unit quaternion."""
    return rotate((q[0], -q[1], -q[2], -q[3]), v)


def subtended_angle(p, a, b):
    """Signed angle the great-circle edge a→b subtends as seen from p (unit vectors)."""
    pa, pb = _cross(p, a), _cross(p, b)
    return math.atan2(_dot(p, _cross(a, b)), _dot(pa, pb))


def inside_sphere_polygon(p, verts):
    """True if the unit vector p lies inside the spherical polygon whose unit-vector vertices are verts (in order)."""
    total = 0.0
    n = len(verts)
    for i in range(n):
        total += subtended_angle(p, verts[i], verts[(i + 1) % n])
    return abs(total) > math.pi

