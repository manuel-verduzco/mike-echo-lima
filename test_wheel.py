import random
import unittest

from phrases import PHRASES, SLICES, deal
from spin_wheel import number_at_pointer, pick_number, target_angle


class WheelTests(unittest.TestCase):
    def test_phrases_are_numbered_1_to_n(self):
        self.assertEqual(sorted(PHRASES), list(range(1, len(PHRASES) + 1)))

    def test_deal_is_distinct_and_valid(self):
        for _ in range(50):
            d = deal()
            expected = len(PHRASES) if SLICES is None else SLICES
            self.assertEqual(len(d), expected)
            self.assertEqual(len(set(d)), expected)
            self.assertTrue(all(n in PHRASES for n in d))

    def test_pick_number_in_range(self):
        rng = random.Random(1)
        for _ in range(500):
            self.assertIn(pick_number(12, rng), range(1, 13))

    def test_target_angle_lands_on_chosen_number(self):
        for count in (2, 8, 12, 24):
            for n in range(1, count + 1):
                self.assertEqual(number_at_pointer(target_angle(n, count), count), n)


if __name__ == "__main__":
    unittest.main()
