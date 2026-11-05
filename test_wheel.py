import random
import unittest

from effects import EFFECT_CHANCE, EFFECTS, JACKPOT_NUMBER, choose_effects
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


class EffectTests(unittest.TestCase):
    def test_landing_on_the_jackpot_number_always_fires_it(self):
        for _ in range(200):
            fx = choose_effects(JACKPOT_NUMBER)
            self.assertIn("jackpot", fx)

    def test_other_numbers_never_get_the_jackpot(self):
        for n in PHRASES:
            if n != JACKPOT_NUMBER:
                self.assertNotIn("jackpot", choose_effects(n, rand=lambda: 0.0))

    def test_random_effect_chance_is_respected(self):
        self.assertEqual(choose_effects(5, rand=lambda: 0.99), [])  # unlucky: nothing
        self.assertEqual(choose_effects(5, rand=lambda: 0.0, randint=lambda a, b: 1), ["rain"])
        fired = sum(1 for _ in range(20000) if choose_effects(5))
        self.assertAlmostEqual(fired / 20000, EFFECT_CHANCE, delta=0.02)

    def test_every_random_effect_can_happen(self):
        seen = set()
        for _ in range(2000):
            seen.update(choose_effects(5))
        self.assertEqual(seen, set(EFFECTS))

    def test_the_jackpot_number_has_a_sentence_to_show(self):
        self.assertIn(JACKPOT_NUMBER, PHRASES)  # the banner shows this sentence


if __name__ == "__main__":
    unittest.main()
