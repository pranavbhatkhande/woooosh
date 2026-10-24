"""Shard assignment, judged-answer folding, and the junk scrubber."""

from __future__ import annotations

import unittest

from pipeline.cores import ensure_cores, token_present
from pipeline.import_judged import fold_answer
from pipeline.llm import slug_for
from pipeline.curated_harvest import missing_hand_items
from pipeline.publish import apply_hand, drop_capped_samples, drop_rejected, pack_shards, prefer_answer_list
from pipeline.year_pin import year_pinned
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

    def test_year_pin_keeps_award_names_and_drops_release_years(self) -> None:
        self.assertFalse(year_pinned({"id": "wd-best-picture", "text": "Name a Best Picture winner"}))
        self.assertFalse(year_pinned({"id": "wd-grammy-album", "text": "Name an Album of the Year winner"}))
        self.assertTrue(year_pinned({"id": "wd-film-2015", "text": "Name a film released in 2015"}))
        self.assertTrue(year_pinned({"id": "wd-film-2015", "text": "Name a film"}))
        self.assertTrue(year_pinned({"id": "wd-gk-x", "text": "Name a Best Picture of 1994"}))
        kept = drop_rejected(
            {
                "wd-film-2015": {"id": "wd-film-2015", "text": "Name a film released in 2015", "answers": [{}] * 900},
                "wd-best-picture": {"id": "wd-best-picture", "text": "Name a Best Picture winner", "answers": [{}] * 90},
                "wd-us-state": {"id": "wd-us-state", "text": "Name a US state", "answers": [{}] * 50},
                "wd-gk-a": {"id": "wd-gk-a", "text": "Name a city in Texas", "answers": [{}] * 200},
            }
        )
        self.assertNotIn("wd-film-2015", kept)
        self.assertIn("wd-best-picture", kept)
        self.assertIn("wd-us-state", kept)

    def test_thin_lists_drop_only_when_the_fat_bank_is_large(self) -> None:
        prompts = {
            f"p{i}": {"id": f"p{i}", "text": f"Name a thing {i}", "answers": [{}] * 100}
            for i in range(300)
        }
        prompts["tiny"] = {"id": "tiny", "text": "Name a US state", "answers": [{}] * 50}
        kept = drop_rejected(prompts)
        self.assertNotIn("tiny", kept)
        self.assertEqual(len(kept), 300)

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

    def test_core_names_are_real_entries_not_substrings(self) -> None:
        answers = [
            {"name": "Hermanubis", "aliases": [], "tier": "taxi", "gem": False},
            {"name": "Osiris myth", "aliases": [], "tier": "stall", "gem": False},
            {"name": "Horus", "aliases": [], "tier": "taxi", "gem": False},
            {"name": "Homer", "aliases": [], "tier": "taxi", "gem": False},
            {"name": "Thor Girl", "aliases": ["Thor"], "tier": "stall", "gem": False},
        ]
        self.assertFalse(token_present(answers, "Anubis"))
        self.assertTrue(token_present(answers, "Horus"))
        self.assertTrue(token_present([{"name": "Ferencvárosi TC", "aliases": []}], "Ferencvaros"))
        prompt = ensure_cores({"id": "wd-gk-god-egypt", "text": "Name an Egyptian god", "answers": answers})
        names = [answer["name"] for answer in prompt["answers"]]
        self.assertIn("Anubis", names)
        self.assertIn("Isis", names)
        self.assertIn("Osiris", names)
        self.assertIn("Osiris myth", names)
        self.assertIn("Hermanubis", names)
        added = {answer["name"]: answer for answer in prompt["answers"]}
        self.assertEqual(added["Anubis"]["tier"], "taxi")
        self.assertFalse(added["Anubis"]["gem"])
        self.assertTrue(token_present(prompt["answers"], "Anubis"))
        greek = ensure_cores({"id": "wd-gk-god-greek", "text": "Name a Greek god", "answers": answers})
        greek_names = [answer["name"] for answer in greek["answers"]]
        self.assertNotIn("Homer", greek_names)
        self.assertIn("Hera", greek_names)
        self.assertIn("Poseidon", greek_names)
        self.assertEqual(added["Horus"]["tier"], "taxi")
        marvel = ensure_cores({"id": "wd-gk-marvel", "text": "Name a Marvel superhero", "answers": answers})
        thor_girl = next(answer for answer in marvel["answers"] if answer["name"] == "Thor Girl")
        self.assertNotIn("Thor", thor_girl["aliases"])
        self.assertTrue(any(answer["name"] == "Thor" and answer["tier"] == "taxi" for answer in marvel["answers"]))
        france = ensure_cores(
            {
                "id": "wd-gk-heritage-fr",
                "text": "Name a World Heritage Site in France",
                "answers": [{"name": "Palace of Versailles", "aliases": ["Versailles Palace"], "tier": "taxi", "gem": False}],
            }
        )
        palace = france["answers"][0]
        self.assertIn("Versailles", palace["aliases"])
        roman = ensure_cores(
            {
                "id": "wd-gk-god-roman",
                "text": "Name a Roman god",
                "answers": [{"name": "Jupiter", "aliases": [], "tier": "taxi", "gem": False}],
            }
        )
        self.assertIn("Juno", [answer["name"] for answer in roman["answers"]])
        self.assertIn("Venus", [answer["name"] for answer in roman["answers"]])

    def test_slug(self) -> None:
        self.assertEqual(slug_for("Name a breakfast pastry"), "breakfast-pastry")


if __name__ == "__main__":
    unittest.main()
