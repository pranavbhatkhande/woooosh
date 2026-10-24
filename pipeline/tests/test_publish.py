"""Shard assignment, judged-answer folding, and the junk scrubber."""

from __future__ import annotations

import unittest

from pipeline.import_judged import fold_answer
from pipeline.llm import slug_for
from pipeline.curated_harvest import missing_hand_items
from pipeline.publish import apply_hand, drop_capped_samples, pack_shards, prefer_answer_list
from pipeline.scrub import scrub_prompt


class PublishTests(unittest.TestCase):
    def test_pack_splits_before_the_byte_cap(self) -> None:
        prompts = {
            "a": {"id": "a", "blob": "x" * 800},
            "b": {"id": "b", "blob": "y" * 800},
        }
        groups = pack_shards(prompts, max_bytes=900)
        self.assertEqual([group["ids"] for group in groups], [["a"], ["b"]])
        self.assertEqual(groups[0]["file"], "data/prompts/0001.json")
        self.assertEqual(groups[1]["file"], "data/prompts/0002.json")

    def test_one_oversized_prompt_stays_in_its_own_file(self) -> None:
        prompts = {
            "big": {"id": "big", "blob": "z" * 5000},
            "small": {"id": "small", "blob": "a"},
        }
        groups = pack_shards(prompts, max_bytes=1000)
        self.assertEqual(groups[0]["ids"], ["big"])
        self.assertEqual(groups[1]["ids"], ["small"])

    def test_smaller_cache_does_not_replace_a_bigger_bank(self) -> None:
        current = {"id": "wd-film-2015", "answers": [{}] * 800}
        incoming = {"id": "wd-film-2015", "answers": [{}] * 69}
        chosen = prefer_answer_list(current, incoming)
        self.assertEqual(len(chosen["answers"]), 800)

    def test_stale_cap_drops_when_a_sibling_is_exhaustive(self) -> None:
        prompts = {
            "wd-film-2015": {"id": "wd-film-2015", "answers": [{}] * 900},
            "wd-film-2016": {"id": "wd-film-2016", "answers": [{}] * 69},
            "wd-us-state": {"id": "wd-us-state", "answers": [{}] * 50},
        }
        kept = drop_capped_samples(prompts)
        self.assertIn("wd-film-2015", kept)
        self.assertNotIn("wd-film-2016", kept)
        self.assertIn("wd-us-state", kept)

    def test_rebuilt_small_city_list_is_kept(self) -> None:
        prompts = {
            "wd-city-fl": {"id": "wd-city-fl", "answers": [{}] * 269},
            "wd-city-ny": {"id": "wd-city-ny", "answers": [{}] * 62},
            "wd-city-mi": {"id": "wd-city-mi", "answers": [{}] * 70},
        }
        kept = drop_capped_samples(prompts, {"wd-city-fl", "wd-city-ny"})
        self.assertIn("wd-city-ny", kept)
        self.assertNotIn("wd-city-mi", kept)

    def test_hand_list_does_not_shrink_a_harvest(self) -> None:
        merged = {"cur-spice": {"id": "cur-spice", "answers": [{}] * 400}}
        apply_hand(merged, [{"id": "cur-spice", "answers": [{}] * 50}])
        self.assertEqual(len(merged["cur-spice"]["answers"]), 400)

    def test_missing_hand_items_skip_names_already_harvested(self) -> None:
        items = [{"label": "Black pepper", "wiki": "Black pepper", "aliases": ["pepper"]}]
        extras = missing_hand_items(
            items,
            [
                {"name": "black pepper", "aliases": ["pepper"]},
                {"name": "Aleppo pepper", "aliases": []},
            ],
        )
        self.assertEqual([item["label"] for item in extras], ["Aleppo pepper"])

    def test_scrub_drops_a_broadcast_listing(self) -> None:
        prompt = {
            "id": "x",
            "answers": [
                {"name": "Parks and Recreation", "aliases": [], "tier": "taxi", "gem": False},
                {"name": "IndyCar Series on NBC", "aliases": ["NBC"], "tier": "escape", "gem": True},
            ],
        }
        cleaned = scrub_prompt(prompt)
        names = [answer["name"] for answer in cleaned["answers"]]
        self.assertEqual(names, ["Parks and Recreation"])

    def test_fold_appends_below_the_gem_and_skips_duplicates(self) -> None:
        prompt = {
            "id": "cur-spice",
            "answers": [
                {"name": "pepper", "aliases": ["black pepper"], "tier": "taxi", "gem": False},
                {"name": "saffron", "aliases": [], "tier": "escape", "gem": True},
            ],
        }
        self.assertEqual(
            fold_answer(prompt, {"canonical": "Aleppo pepper", "tier": "escape"}),
            "added",
        )
        added = prompt["answers"][-2]
        self.assertEqual(added["name"], "Aleppo pepper")
        self.assertEqual(added["tier"], "apogee")
        self.assertFalse(added["gem"])
        self.assertTrue(prompt["answers"][-1]["gem"])
        self.assertEqual(fold_answer(prompt, {"canonical": "black pepper", "tier": "taxi"}), "skipped")
        self.assertEqual(fold_answer(prompt, {"canonical": "shit", "tier": "taxi"}), "rejected")

    def test_slug(self) -> None:
        self.assertEqual(slug_for("Name a breakfast pastry"), "breakfast-pastry")


if __name__ == "__main__":
    unittest.main()
