import json
import os
import random
import re
import unittest

from effects import (EFFECT_CHANCE, EFFECTS, JACKPOT_NUMBER, MILESTONE_MESSAGE, MILESTONE_SPIN, MILESTONE_TITLE,
                     SECRET_GAP_MS, SECRET_TAPS, choose_effects, is_milestone, register_tap)
from counters import DB_KEY, DB_URL, LIVE_HOST, counts_url, db_namespace, record_spin_url, total_url
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


class MilestoneTests(unittest.TestCase):
    def test_only_the_exact_milestone_spin_wins(self):
        self.assertTrue(is_milestone(MILESTONE_SPIN))
        for total in (0, 1, 999, 1001, 2000):
            self.assertFalse(is_milestone(total))

    def test_the_milestone_is_spin_number_1000(self):
        self.assertEqual(MILESTONE_SPIN, 1000)

    def test_there_is_a_message_to_show(self):
        self.assertTrue(MILESTONE_TITLE.strip())
        self.assertTrue(MILESTONE_MESSAGE.strip())


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
        self.stats_html, self.stats_py = read("stats.html"), read("stats.py")
        self.pattern = re.compile(r"\.(?:py|json|toml)\?v=(\d+)")

    def test_every_game_file_uses_the_same_cache_version(self):
        versions = set(self.pattern.findall(self.html) + self.pattern.findall(self.toml)
                       + self.pattern.findall(self.stats_html))
        self.assertEqual(len(versions), 1,
                         "different ?v= numbers found %s - run: python bump_version.py" % sorted(versions))

    def test_every_local_module_web_py_imports_is_listed_in_pyscript_toml(self):
        for name in re.findall(r"^from (\w+) import", self.web + "\n" + self.stats_py, flags=re.M):
            if os.path.isfile(os.path.join(self.here, name + ".py")):
                self.assertIn('"./%s.py?v=' % name, self.toml,
                              "%s.py is imported by web.py or stats.py but missing from pyscript.toml" % name)

    def test_phrases_json_is_listed_in_pyscript_toml(self):
        self.assertIn('"./phrases.json?v=', self.toml)


class DatabaseConfigTests(unittest.TestCase):
    """The counters live in Supabase. These checks keep the setup safe and in step with the sentences."""

    def project_files(self):
        here = os.path.dirname(os.path.abspath(__file__))
        for folder, dirs, files in os.walk(here):
            dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", "sounds")]
            for name in files:
                if name.endswith((".py", ".html", ".json", ".sql", ".toml", ".yml", ".sh", ".js")) and name != "test_wheel.py":
                    path = os.path.join(folder, name)
                    with open(path, encoding="utf-8") as f:
                        yield name, f.read()

    def test_the_real_site_and_testing_count_into_separate_rows(self):
        self.assertEqual(db_namespace(LIVE_HOST), "live")
        for host in ("localhost", "127.0.0.1", "192.168.1.20"):
            self.assertEqual(db_namespace(host), "dev")

    def test_the_key_in_the_code_is_the_public_one(self):
        self.assertTrue(DB_KEY.startswith("sb_publishable_"))
        self.assertTrue(DB_URL.startswith("https://") and DB_URL.endswith(".supabase.co"))

    def test_no_secret_database_key_is_anywhere_in_the_project(self):
        # looks for the SHAPE of a real secret key (not the words, which the docs may mention as a warning)
        secret_key = re.compile(r"sb_secret_[A-Za-z0-9_\-]{16,}")
        jwt = re.compile(r"eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}")  # old-style keys, incl. service_role
        for name, text in self.project_files():
            self.assertIsNone(secret_key.search(text), name + " contains what looks like a Supabase secret key")
            self.assertIsNone(jwt.search(text), name + " contains what looks like a JWT / legacy API key")

    def test_the_guard_really_recognises_a_secret_key(self):
        secret_key = re.compile(r"sb_secret_[A-Za-z0-9_\-]{16,}")
        self.assertIsNotNone(secret_key.search("KEY = 'sb_secret_lRSVExampleExampleExample1234'"))
        self.assertIsNone(secret_key.search("never put a key that starts sb_secret_ in the repository"))

    def test_the_addresses_point_at_the_project(self):
        self.assertEqual(record_spin_url(), DB_URL + "/rest/v1/rpc/record_spin")
        self.assertIn("spin_totals", total_url("live"))
        self.assertIn("namespace=eq.live", total_url("live"))
        self.assertIn("sentence_counts", counts_url("dev"))
        self.assertIn("namespace=eq.dev", counts_url("dev"))

    def test_the_database_has_a_row_for_every_sentence(self):
        # supabase_setup.sql creates rows 1..106. If you add sentences, add rows too (see that file).
        self.assertLessEqual(max(PHRASES), 106, "more sentences than database rows: extend supabase_setup.sql")

    def test_the_sql_locks_the_tables_down(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "supabase_setup.sql"), encoding="utf-8") as f:
            sql = f.read().lower()
        self.assertEqual(sql.count("enable row level security"), 2)      # both tables
        self.assertIn("revoke all on public.spin_totals, public.sentence_counts from anon, authenticated", sql)
        self.assertIn("grant select on public.spin_totals, public.sentence_counts to anon", sql)
        self.assertIn("security definer", sql)                            # the add-1 function runs with its own rights
        self.assertIn("grant execute on function public.record_spin(text, integer) to anon", sql)
        for forbidden in ("to anon, authenticated", "grant insert", "grant update", "grant delete", "grant all"):
            self.assertNotIn(forbidden, sql, "the public key must never be allowed to write: " + forbidden)


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
