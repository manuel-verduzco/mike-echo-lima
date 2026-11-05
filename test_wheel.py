import random
import unittest

from phrases import GROUPS, PHRASES, deal, group_index, label, random_number
from spin_wheel import number_at_pointer, pick_number, target_angle


class WheelTests(unittest.TestCase):
    def test_phrases_are_numbered_1_to_n(self):
        self.assertEqual(sorted(PHRASES), list(range(1, len(PHRASES) + 1)))

    def test_groups_cover_every_number_once(self):
        for _ in range(20):
            groups = deal()
            self.assertEqual(len(groups), GROUPS)
            flat = sorted(n for g in groups for n in g)
            self.assertEqual(flat, sorted(PHRASES))
            sizes = {len(g) for g in groups}
            self.assertLessEqual(max(sizes) - min(sizes), 1)

    def test_every_number_can_be_chosen_and_has_a_slice(self):
        groups = deal()
        for n in PHRASES:
            self.assertIn(n, groups[group_index(groups, n)])
        rng_seen = {random_number() for _ in range(5000)}
        self.assertGreater(len(rng_seen), 0.95 * len(PHRASES))

    def test_label(self):
        self.assertEqual(label([7]), "7")
        self.assertEqual(label([1, 2, 3, 4, 5]), "1-5")

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
