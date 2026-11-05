import json
import os
import random
import re
import unittest

from effects import EFFECT_CHANCE, EFFECTS, JACKPOT_NUMBER, SECRET_GAP_MS, SECRET_TAPS, choose_effects, register_tap
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


class SecretTapTests(unittest.TestCase):
    def run_taps(self, times):
        taps, triggered = [], []
        for ms in times:
            taps, hit = register_tap(taps, ms)
            triggered.append(hit)
        return triggered

    def test_five_quick_taps_trigger_it(self):
        self.assertEqual(self.run_taps([0, 300, 600, 900, 1200]), [False] * 4 + [True])

    def test_four_taps_are_not_enough(self):
        self.assertFalse(any(self.run_taps([0, 200, 400, 600])))

    def test_a_pause_restarts_the_count(self):
        gap = SECRET_GAP_MS + 1
        self.assertFalse(any(self.run_taps([0, 200, 400, 400 + gap, 400 + gap + 200])))
        # ...but five fresh quick taps after a pause do work
        late = 10_000
        self.assertTrue(self.run_taps([0, 200, late, late + 100, late + 200, late + 300, late + 400])[-1])

    def test_it_resets_after_triggering(self):
        quick = [i * 200 for i in range(SECRET_TAPS * 2)]
        self.assertEqual(self.run_taps(quick).count(True), 2)  # 10 taps = two triggers


class WebsiteFilesTests(unittest.TestCase):
    """Guards against the "half old, half new files" error that cached versions can cause."""

    def setUp(self):
        self.here = os.path.dirname(os.path.abspath(__file__))

        def read(name):
            with open(os.path.join(self.here, name), encoding="utf-8") as f:
                return f.read()

        self.html, self.toml, self.web = read("index.html"), read("pyscript.toml"), read("web.py")
        self.pattern = re.compile(r"\.(?:py|json|toml)\?v=(\d+)")

    def test_every_game_file_uses_the_same_cache_version(self):
        versions = set(self.pattern.findall(self.html) + self.pattern.findall(self.toml))
        self.assertEqual(len(versions), 1,
                         "different ?v= numbers found %s - run: python bump_version.py" % sorted(versions))

    def test_every_local_module_web_py_imports_is_listed_in_pyscript_toml(self):
        for name in re.findall(r"^from (\w+) import", self.web, flags=re.M):
            if os.path.isfile(os.path.join(self.here, name + ".py")):
                self.assertIn('"./%s.py?v=' % name, self.toml,
                              "%s.py is imported by web.py but missing from pyscript.toml" % name)

    def test_phrases_json_is_listed_in_pyscript_toml(self):
        self.assertIn('"./phrases.json?v=', self.toml)


class SoundManifestTests(unittest.TestCase):
    """Catches typos in sounds.json before they reach the website."""

    def setUp(self):
        here = os.path.dirname(os.path.abspath(__file__))
        self.folder = os.path.join(here, "sounds")
        with open(os.path.join(here, "sounds.json"), encoding="utf-8") as f:
            self.manifest = json.load(f)

    def test_every_entry_is_a_real_sentence_and_a_real_file(self):
        for key, name in self.manifest.items():
            self.assertTrue(key.isdigit(), "%r is not a sentence number" % key)
            self.assertIn(int(key), PHRASES, "sentence %s does not exist in phrases.json" % key)
            self.assertTrue(isinstance(name, str) and name, "sentence %s has no file name" % key)
            self.assertNotIn("/", name)
            self.assertNotIn("..", name)
            self.assertTrue(os.path.isfile(os.path.join(self.folder, name)),
                            "sounds/%s (for sentence %s) does not exist - check the spelling" % (name, key))


if __name__ == "__main__":
    unittest.main()
