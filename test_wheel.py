import json
import os
import random
import re
import tempfile
import unittest

from effects import (EFFECT_CHANCE, EFFECTS, JACKPOT_NUMBER, MILESTONE_MESSAGE, MILESTONE_SPIN, MILESTONE_TITLE,
                     SECRET_GAP_MS, SECRET_TAPS, choose_effects, is_milestone, register_tap)
from counters import LIVE_NAMESPACE, LIVE_STATS_URL, LOCAL_STATS_URL, TOTAL_KEY, namespace_for, sentence_key, stats_urls
from phrases import GROUPS, PHRASES, deal, group_index, label, random_number
from spin_wheel import number_at_pointer, pick_number, target_angle
from timeutil import ago_text, iso_to_seconds
from make_baseline import build, describe, make_counts
from update_stats import collect, load_baseline, same_numbers, update


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


class CounterNameTests(unittest.TestCase):
    def test_real_site_and_testing_use_different_counters(self):
        self.assertEqual(namespace_for("manuel-verduzco.github.io"), LIVE_NAMESPACE)
        for host in ("localhost", "127.0.0.1", "192.168.1.20"):
            self.assertEqual(namespace_for(host), LIVE_NAMESPACE + "-dev")

    def test_every_sentence_has_a_valid_counter_name(self):
        names = {sentence_key(n) for n in PHRASES}
        self.assertEqual(len(names), len(PHRASES))  # all different
        for name in names:
            self.assertTrue(3 <= len(name) <= 64)  # the service rejects shorter or longer names
            self.assertRegex(name, r"^[A-Za-z0-9_.-]+$")


class TimeHelperTests(unittest.TestCase):
    def test_iso_text_turns_into_the_right_number_of_seconds(self):
        from datetime import datetime, timezone
        for iso in ("1970-01-01T00:00:00Z", "2000-02-29T23:59:59Z", "2026-11-06T11:40:12Z", "2026-03-01T00:00:00Z",
                    "2026-01-31T12:00:00.123Z", "2024-12-31T23:59:59Z", "2100-03-01T00:00:00Z"):
            real = datetime.strptime(iso[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()
            self.assertEqual(iso_to_seconds(iso), int(real), iso)

    def test_ago_text(self):
        self.assertEqual(ago_text(0), "just now")
        self.assertEqual(ago_text(59), "just now")
        self.assertEqual(ago_text(60), "1 minute ago")
        self.assertEqual(ago_text(5 * 60 + 30), "5 minutes ago")
        self.assertEqual(ago_text(3600), "1 hour ago")
        self.assertEqual(ago_text(7 * 3600), "7 hours ago")
        self.assertEqual(ago_text(3 * 86400), "3 days ago")


class StatsLocationTests(unittest.TestCase):
    def test_the_real_site_reads_the_stats_branch_then_falls_back_to_the_shipped_file(self):
        self.assertEqual(stats_urls(True), [LIVE_STATS_URL, LOCAL_STATS_URL])
        self.assertEqual(stats_urls(False), [LOCAL_STATS_URL])

    def test_the_live_address_points_at_the_stats_data_branch(self):
        self.assertIn("/stats-data/stats.json", LIVE_STATS_URL)
        self.assertTrue(LIVE_STATS_URL.startswith("https://raw.githubusercontent.com/"))

    def test_the_schedule_is_no_faster_than_github_allows(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, ".github", "workflows", "update-stats.yml"), encoding="utf-8") as f:
            text = f.read()
        cron = re.search(r'cron:\s*"([^"]+)"', text).group(1)
        minutes = cron.split()[0]
        if "/" in minutes:
            gap = int(minutes.split("/")[1])  # a step such as */10
        else:
            slots = sorted(int(m) for m in minutes.split(","))  # an explicit list such as 5,15,25
            gap = min((b - a) % 60 or 60 for a, b in zip(slots, slots[1:] + slots[:1]))
        self.assertGreaterEqual(gap, 5, "GitHub does not run scheduled workflows more often than every 5 minutes")

    def test_the_workflow_uses_the_saving_script_that_exists(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, ".github", "workflows", "update-stats.yml"), encoding="utf-8") as f:
            self.assertIn(".github/scripts/save_stats.sh", f.read())
        self.assertTrue(os.path.isfile(os.path.join(here, ".github", "scripts", "save_stats.sh")))


class StatsSnapshotTests(unittest.TestCase):
    def fake_service(self, values, fail_on=None):
        """A pretend counter service: {(namespace, key): number}; missing keys read as 0."""
        calls = []

        def fetch(namespace, key):
            calls.append((namespace, key))
            if key == fail_on:
                raise RuntimeError("the counter service is down")
            return values.get((namespace, key), 0)

        return fetch, calls

    def test_collect_reads_the_total_and_every_sentence(self):
        values = {("ns", TOTAL_KEY): 50, ("ns", sentence_key(1)): 3, ("ns", sentence_key(37)): 9}
        fetch, calls = self.fake_service(values)
        data = collect("ns", sorted(PHRASES), fetch=fetch, sleep=lambda s: None)
        self.assertEqual(data["total"], 50)
        self.assertEqual(data["counted"], 12)
        self.assertEqual(sorted(data["counts"], key=int), [str(n) for n in sorted(PHRASES)])
        self.assertEqual(data["counts"]["37"], 9)
        self.assertEqual(data["counts"]["2"], 0)
        self.assertEqual(len(calls), len(PHRASES) + 1)

    def test_update_writes_then_leaves_an_unchanged_file_alone(self):
        fetch, _ = self.fake_service({("ns", sentence_key(5)): 4, ("ns", TOTAL_KEY): 10})
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "stats.json")
            self.assertEqual(update(path, "ns", [1, 5], fetch=fetch, sleep=lambda s: None, now=lambda: "T1"), "updated")
            first = open(path, encoding="utf-8").read()
            self.assertEqual(json.loads(first)["updated"], "T1")
            self.assertEqual(json.loads(first)["counts"], {"1": 0, "5": 4})
            # same numbers again: nothing is rewritten, so no pointless commit
            self.assertEqual(update(path, "ns", [1, 5], fetch=fetch, sleep=lambda s: None, now=lambda: "T2"), "unchanged")
            self.assertEqual(open(path, encoding="utf-8").read(), first)

    def test_new_spins_update_the_file(self):
        values = {("ns", sentence_key(5)): 4, ("ns", TOTAL_KEY): 10}
        fetch, _ = self.fake_service(values)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "stats.json")
            update(path, "ns", [1, 5], fetch=fetch, sleep=lambda s: None, now=lambda: "T1")
            values[("ns", sentence_key(5))] = 5
            self.assertEqual(update(path, "ns", [1, 5], fetch=fetch, sleep=lambda s: None, now=lambda: "T2"), "updated")
            with open(path, encoding="utf-8") as f:
                self.assertEqual(json.load(f)["counts"]["5"], 5)

    def test_a_failure_never_overwrites_good_numbers(self):
        good, _ = self.fake_service({("ns", sentence_key(5)): 4})
        broken, _ = self.fake_service({}, fail_on=sentence_key(5))
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "stats.json")
            update(path, "ns", [1, 5], fetch=good, sleep=lambda s: None, now=lambda: "T1")
            before = open(path, encoding="utf-8").read()
            with self.assertRaises(RuntimeError):
                update(path, "ns", [1, 5], fetch=broken, sleep=lambda s: None, now=lambda: "T2")
            self.assertEqual(open(path, encoding="utf-8").read(), before)

    def test_same_numbers_ignores_the_updated_time(self):
        a = {"updated": "T1", "total": 1, "counted": 1, "counts": {"1": 1}}
        self.assertTrue(same_numbers(a, {"updated": "T2", "total": 1, "counted": 1, "counts": {"1": 1}}))
        self.assertFalse(same_numbers(a, {"total": 2, "counted": 1, "counts": {"1": 1}}))


class BaselineTests(unittest.TestCase):
    def test_the_stand_in_spins_add_up_to_the_earlier_total(self):
        counts = make_counts(793, sorted(PHRASES), seed=1)
        self.assertEqual(sum(counts.values()), 793)
        self.assertEqual(sorted(counts, key=int), [str(n) for n in sorted(PHRASES)])

    def test_the_spread_is_repeatable_and_roughly_even(self):
        a = make_counts(10_600, sorted(PHRASES), seed=7)
        self.assertEqual(a, make_counts(10_600, sorted(PHRASES), seed=7))   # same seed, same numbers
        self.assertNotEqual(a, make_counts(10_600, sorted(PHRASES), seed=8))
        expected = 10_600 / len(PHRASES)  # 100 each
        self.assertLess(max(a.values()), expected * 1.6)
        self.assertGreater(min(a.values()), expected * 0.5)

    def test_a_pinned_sentence_gets_exactly_its_number_and_the_total_still_adds_up(self):
        counts = make_counts(793, sorted(PHRASES), seed=2026, pins={"1": 12})
        self.assertEqual(counts["1"], 12)
        self.assertEqual(sum(counts.values()), 793)
        self.assertEqual(len(counts), len(PHRASES))
        # the others share out the rest evenly, so nothing looks absurd next to the pinned one
        others = [v for k, v in counts.items() if k != "1"]
        self.assertGreaterEqual(min(others), 1)
        self.assertLessEqual(max(others), 20)

    def test_the_default_spread_looks_like_real_random_spins(self):
        counts = make_counts(793, sorted(PHRASES), seed=2026, pins={"1": 12})
        info = describe(counts, {"1": 12})
        self.assertAlmostEqual(info["average"], 793 / 106, places=1)
        self.assertGreater(info["spread_ratio"], 0.7)   # real random spins give about 1.0
        self.assertLess(info["spread_ratio"], 1.4)
        self.assertLessEqual(info["ranks"]["1"], 15)    # #1 at 12 sits in the upper part, not at the very top
        self.assertGreater(info["ranks"]["1"], 3)

    def test_bad_pins_are_refused(self):
        with self.assertRaises(ValueError):
            make_counts(10, [1, 2, 3], seed=1, pins={"1": 11})      # more than the total
        with self.assertRaises(ValueError):
            make_counts(10, [1, 2, 3], seed=1, pins={"99": 1})      # not a sentence

    def test_the_file_says_plainly_that_it_is_not_real_data(self):
        data = build(50, [1, 2, 3], seed=1, now=lambda: "T")
        self.assertTrue(data["estimated"])
        self.assertIn("NOT real", data["note"])
        self.assertEqual(data["spins"], 50)
        self.assertEqual(sum(data["counts"].values()), 50)

    def test_the_snapshot_adds_the_baseline_to_the_real_counts(self):
        values = {("ns", TOTAL_KEY): 100, ("ns", sentence_key(1)): 5, ("ns", sentence_key(2)): 0}
        fetch = lambda ns, key: values.get((ns, key), 0)
        data = collect("ns", [1, 2], fetch=fetch, sleep=lambda s: None, baseline=({"1": 40, "2": 55}, 95))
        self.assertEqual(data["counts"], {"1": 45, "2": 55})
        self.assertEqual(data["counted"], 100)
        self.assertEqual(data["total"], 100)
        self.assertEqual(data["baseline"], 95)

    def test_no_baseline_file_means_no_extra_numbers(self):
        self.assertEqual(load_baseline("this-file-does-not-exist.json"), ({}, 0))
        data = collect("ns", [1], fetch=lambda ns, key: 3, sleep=lambda s: None, baseline=None)
        self.assertEqual(data["baseline"], 0)


class StatsFileTests(unittest.TestCase):
    def test_the_saved_snapshot_covers_every_sentence(self):
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "stats.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(sorted(data["counts"], key=int), [str(n) for n in sorted(PHRASES)])
        self.assertTrue(all(isinstance(v, int) and v >= 0 for v in data["counts"].values()))
        self.assertEqual(data["counted"], sum(data["counts"].values()))


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
