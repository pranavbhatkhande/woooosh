import unittest

from pipeline.normalize import normalize
from pipeline.profanity import contains_profanity
from pipeline.quality import evaluate, repair_answers
from pipeline.tiering import assign_tiers


def _row(name, popularity, aliases=None):
    return {"name": name, "popularity": popularity, "aliases": aliases or []}


class QualityTests(unittest.TestCase):
    def test_profanity_is_token_based(self):
        self.assertTrue(contains_profanity("Fucking"))
        self.assertFalse(contains_profanity("Scunthorpe"))
        self.assertFalse(contains_profanity("cocktail"))
        self.assertFalse(contains_profanity("Assam"))
        self.assertFalse(contains_profanity("classical"))
        self.assertTrue(contains_profanity("Sex and the City"))

    def test_repair_drops_alias_and_near_canonical_collisions(self):
        rows = repair_answers([
            _row("Gambia", 50, ["Zambia"]),
            _row("Zambia", 40, ["ZM"]),
            _row("Cat", 30, ["cats"]),
            _row("Cats", 10, ["feline"]),
            _row("France", 80, ["French Republic", "France"]),
        ])
        names = {row["name"] for row in rows}
        self.assertIn("Gambia", names)
        self.assertNotIn("Zambia", names)
        self.assertTrue("Cat" in names or "Cats" in names)
        self.assertFalse({"Cat", "Cats"} <= names)
        gambia = next(row for row in rows if row["name"] == "Gambia")
        self.assertNotIn("Zambia", gambia["aliases"])
        france = next(row for row in rows if row["name"] == "France")
        self.assertEqual(normalize("French Republic"), normalize(france["aliases"][0]))

    def test_evaluate_accepts_a_spread_and_rejects_a_short_list(self):
        answers = [{"name": f"n{i:03d}", "popularity": 100 - i, "aliases": []} for i in range(50)]
        assign_tiers(answers)
        prompt = {
            "text": "Name a test answer from the bench",
            "answers": answers,
        }
        self.assertEqual(evaluate(prompt), [])
        self.assertTrue(any(issue.startswith("too-few") for issue in evaluate({"text": prompt["text"], "answers": answers[:10]})))


if __name__ == "__main__":
    unittest.main()
