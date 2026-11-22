import math
import unittest

import plate_lookup as pl


def square(lat0, lon0, half):
    corners = [(lat0 - half, lon0 - half), (lat0 - half, lon0 + half), (lat0 + half, lon0 + half), (lat0 + half, lon0 - half)]
    return [pl.lonlat_to_xyz(la, lo) for la, lo in corners]


class PointInPolygon(unittest.TestCase):
    def test_point_inside_and_outside(self):
        poly = square(0, 0, 10)
        self.assertTrue(pl.inside_sphere_polygon(pl.lonlat_to_xyz(0, 0), poly))
        self.assertTrue(pl.inside_sphere_polygon(pl.lonlat_to_xyz(5, -5), poly))
        self.assertFalse(pl.inside_sphere_polygon(pl.lonlat_to_xyz(0, 30), poly))
        self.assertFalse(pl.inside_sphere_polygon(pl.lonlat_to_xyz(20, 0), poly))

    def test_orientation_does_not_matter(self):
        poly = square(40, -120, 5)
        p = pl.lonlat_to_xyz(41, -119)
        self.assertTrue(pl.inside_sphere_polygon(p, poly))
        self.assertTrue(pl.inside_sphere_polygon(p, list(reversed(poly))))

    def test_across_the_dateline(self):
        poly = square(0, 180, 8)
        self.assertTrue(pl.inside_sphere_polygon(pl.lonlat_to_xyz(0, 175), poly))
        self.assertTrue(pl.inside_sphere_polygon(pl.lonlat_to_xyz(0, -175), poly))
        self.assertFalse(pl.inside_sphere_polygon(pl.lonlat_to_xyz(0, 150), poly))


class Rotation(unittest.TestCase):
    def test_unrotate_undoes_rotate(self):
        ang = math.radians(37)
        q = (math.cos(ang / 2), math.sin(ang / 2) * 0.6, math.sin(ang / 2) * 0.8, 0.0)   # unit: 0.36 + 0.64 = 1
        v = pl.unit((0.3, -0.5, 0.8))
        back = pl.unrotate(q, pl.rotate(q, v))
        for a, b in zip(back, v):
            self.assertAlmostEqual(a, b, places=12)

    def test_rotated_polygon_test_round_trip(self):
        # a plate rotated 30 degrees about the pole moves a point 20 degrees east; testing the present-day polygon after
        # undoing that rotation finds the point inside the polygon that was moved there
        ang = math.radians(30)
        q = (math.cos(ang / 2), 0.0, 0.0, math.sin(ang / 2))
        poly = square(0, 0, 10)
        moved = pl.rotate(q, pl.lonlat_to_xyz(0, 0))
        self.assertTrue(pl.inside_sphere_polygon(pl.unrotate(q, moved), poly))
        self.assertFalse(pl.inside_sphere_polygon(moved, poly))


if __name__ == "__main__":
    unittest.main()
