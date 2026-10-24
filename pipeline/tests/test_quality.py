import json
import unittest
from pathlib import Path

from pipeline.normalize import normalize
from pipeline.profanity import is_profane
from pipeline.quality import lint_prompt, repair_answers

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests" / "fixtures" / "normalize-cases.json").read_text())


class NormalizeTests(unittest.TestCase):
    def test_matches_javascript_fixtures(self):
        for raw, expected in CASES:
            self.assertEqual(normalize(raw), expected, raw)


class QualityTests(unittest.TestCase):
    def test_profanity_is_token_based(self):
        self.assertTrue(is_profane("what the fuck"))
        self.assertFalse(is_profane("Assam"))
        self.assertFalse(is_profane("classic"))
        self.assertFalse(is_profane("Scunthorpe"))

    def test_repair_merges_plurals_and_drops_colliding_aliases(self):
        repaired = repair_answers(
            [
                {"name": "Shark", "aliases": [], "pop": 10, "sitelinks": 20},
                {"name": "Sharks", "aliases": ["great white"], "pop": 4, "sitelinks": 8},
                {"name": "Mercury", "aliases": ["quicksilver"], "pop": 9, "sitelinks": 30},
                {"name": "Hermes", "aliases": ["quicksilver"], "pop": 8, "sitelinks": 28},
            ]
        )
        names = {answer["name"] for answer in repaired}
        self.assertIn("Shark", names)
        self.assertNotIn("Sharks", names)
        shark = next(answer for answer in repaired if answer["name"] == "Shark")
        self.assertIn("Sharks", shark["aliases"])
        for answer in repaired:
            self.assertNotIn("quicksilver", [alias.lower() for alias in answer["aliases"]])

    def test_lint_flags_a_short_ambiguous_prompt(self):
        errors = lint_prompt(
            {
                "id": "x",
                "text": "Name something or whatever?",
                "category": "misc",
                "source": "llm",
                "answers": [{"name": "Thing", "aliases": [], "tier": "taxi", "gem": False}],
            }
        )
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
