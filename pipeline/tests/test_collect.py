"""Category walks stay on the answer pages unless a harvest asks for subcategories."""

from __future__ import annotations

import unittest
from unittest import mock

from pipeline.collect import collect_categories, place_answer_category
from pipeline.make_prompt import _has_name, build_prompt, latin_binomial, taxonomic_name


class CollectTests(unittest.TestCase):
    def test_latin_binomials_drop_and_common_names_stay(self) -> None:
        self.assertTrue(latin_binomial("Rosa acicularis"))
        self.assertTrue(latin_binomial("Abies alba"))
        self.assertTrue(latin_binomial("Acer campestre"))
        self.assertFalse(latin_binomial("Japanese iris"))
        self.assertFalse(latin_binomial("Red maple"))
        self.assertFalse(latin_binomial("Rose"))
        self.assertFalse(latin_binomial("Baby Ruth"))
        self.assertFalse(latin_binomial("Great white shark"))
        self.assertTrue(taxonomic_name("Iris x germanica"))
        self.assertTrue(taxonomic_name("Hibiscus ×rosa-sinensis"))
        self.assertTrue(taxonomic_name("Iris sect. Scorpiris"))
        self.assertFalse(taxonomic_name("Japanese iris"))


    def test_thin_category_does_not_walk_subcategories(self) -> None:
        def pages(title: str) -> list[dict]:
            if title.endswith("Parent"):
                return [{"qid": f"Q{i}", "wiki": f"Club {i}"} for i in range(50)]
            return [{"qid": "Qseason", "wiki": "1999 season"}]

        with mock.patch("pipeline.collect.category_pages", side_effect=pages) as seen:
            with mock.patch("pipeline.collect.category_subcats", return_value=["Category:Club seasons"]) as subs:
                found = collect_categories(["Parent"])
        self.assertEqual(len(found), 50)
        subs.assert_not_called()
        self.assertEqual(seen.call_args_list[0].args[0], "Category:Parent")

    def test_city_subcats_contribute_titles_without_being_walked(self) -> None:
        self.assertTrue(place_answer_category("Category:Detroit"))
        self.assertFalse(place_answer_category("Category:Cities in Michigan by county"))

        def pages(title: str) -> list[dict]:
            return [{"qid": "Qlist", "wiki": "List of cities in Michigan"}]

        def subs(title: str) -> list[str]:
            return ["Category:Detroit", "Category:Cities in Michigan by county", "Category:Ann Arbor, Michigan"]

        with mock.patch("pipeline.collect.category_pages", side_effect=pages) as seen:
            with mock.patch("pipeline.collect.category_subcats", side_effect=subs):
                with mock.patch("pipeline.collect.resolve_qids", side_effect=lambda items: items):
                    found = collect_categories(["Cities in Michigan"], places_from_subcats=True, subcat_below=40)
        self.assertEqual(seen.call_count, 1)
        self.assertEqual([item["wiki"] for item in found], ["Detroit", "Ann Arbor, Michigan"])

    def test_profane_alias_does_not_reject_the_prompt(self) -> None:
        items = []
        for index in range(45):
            items.append(
                {
                    "label": f"Film {index:02d}",
                    "wiki": f"Film {index:02d}",
                    "sitelinks": 80 - index,
                    "aliases": ["shit"] if index == 0 else [],
                }
            )
        items[0]["label"] = "Inception"
        items[0]["wiki"] = "Inception"
        prompt, reason = build_prompt(
            {
                "id": "wd-film-x",
                "text": "Name a film released in 2010",
                "category": "film",
                "must": ["Inception"],
            },
            items,
        )
        self.assertTrue(prompt, reason)
        aliases = [alias for answer in prompt["answers"] for alias in answer["aliases"]]
        self.assertNotIn("shit", [alias.lower() for alias in aliases])

    def test_compact_title_collision_keeps_the_prompt(self) -> None:
        items = [
            {"label": "After Hours", "wiki": "After Hours", "sitelinks": 40, "aliases": []},
            {"label": "Afterhours", "wiki": "Afterhours", "sitelinks": 8, "aliases": []},
        ]
        for index in range(40):
            items.append(
                {"label": f"Album {index:02d}", "wiki": f"Album {index:02d}", "sitelinks": 20, "aliases": []}
            )
        prompt, reason = build_prompt(
            {
                "id": "wd-album-x",
                "text": "Name an album released in 2017",
                "category": "music",
                "must": ["After Hours"],
            },
            items,
        )
        self.assertTrue(prompt, reason)
        names = [answer["name"] for answer in prompt["answers"]]
        self.assertIn("After Hours", names)
        self.assertNotIn("Afterhours", names)

    def test_required_name_matches_without_accents(self) -> None:
        answers = [
            {"name": "Kīlauea"},
            {"name": "Ferencvárosi TC"},
            {"name": "Malé"},
            {"name": "FK Crvena zvezda", "aliases": ["Red Star Belgrade"]},
        ]
        self.assertTrue(_has_name(answers, "Kilauea"))
        self.assertTrue(_has_name(answers, "Ferencvaros"))
        self.assertTrue(_has_name(answers, "Male"))
        self.assertTrue(_has_name(answers, "Red Star"))
        self.assertFalse(_has_name(answers, "Etna"))


if __name__ == "__main__":
    unittest.main()
