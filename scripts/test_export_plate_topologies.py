import unittest
from export_plate_topologies import quantise, encode_line, frame_size_bytes, BOUNDARY_TYPES


class QuantiseTest(unittest.TestCase):
    def test_rounds_to_hundredths_and_wraps_longitude(self):
        self.assertEqual(quantise(38.4849, -122.4473), (3848, -12245))
        self.assertEqual(quantise(0, 190.0), (0, -17000))
        self.assertEqual(quantise(0, -180.0), (0, -18000))


class EncodeLineTest(unittest.TestCase):
    def test_absolute_start_then_deltas(self):
        self.assertEqual(encode_line([(10, 20), (10.5, 20.25)]), [1000, 2000, 50, 25])

    def test_drops_repeated_points(self):
        self.assertEqual(encode_line([(10, 20), (10, 20), (10.5, 20)]), [1000, 2000, 50, 0])

    def test_empty(self):
        self.assertEqual(encode_line([]), [])


class FrameTest(unittest.TestCase):
    def test_size_is_compact_json_bytes(self):
        self.assertEqual(frame_size_bytes([[0, [1, 2]]]), len(b"[[0,[1,2]]]"))

    def test_boundary_types_are_the_drawn_gpml_types(self):
        self.assertIn("SubductionZone", BOUNDARY_TYPES)
        self.assertIn("Transform", BOUNDARY_TYPES)
        self.assertIn("MidOceanRidge", BOUNDARY_TYPES)


if __name__ == "__main__":
    unittest.main()
