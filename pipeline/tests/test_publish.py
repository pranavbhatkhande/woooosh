"""Shard assignment, judged-answer folding, and the junk scrubber."""

from __future__ import annotations

import unittest

from pipeline.import_judged import fold_answer
from pipeline.llm import slug_for
from pipeline.publish import assign_shards
from pipeline.scrub import scrub_prompt


class PublishTests(unittest.TestCase):
    def test_new_ids_fill_the_last_shard_then_a_new_file(self) -> None:
        old = {"shards": [{"file": "data/prompts/0001.json", "ids": ["a", "b"]}]}
        groups = assign_shards(old, {"a", "b", "c"})
        self.assertEqual(groups[0]["ids"], ["a", "b", "c"])
        self.assertEqual(len(groups), 1)

    def test_full_shard_opens_the_next_free_name(self) -> None:
        old = {"shards": [{"file": "data/prompts/0001.json", "ids": [f"p{i}" for i in range(45)]}]}
        ids = set(old["shards"][0]["ids"]) | {"new"}
        groups = assign_shards(old, ids)
        self.assertEqual(groups[1]["file"], "data/prompts/0002.json")
        self.assertEqual(groups[1]["ids"], ["new"])

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
