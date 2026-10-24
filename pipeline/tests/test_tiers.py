import unittest

from pipeline.tiers import (
    allocate,
    assign_by_popularity,
    assign_ordered,
    tier_for_familiarity,
    tier_for_rarity,
)


class TierTests(unittest.TestCase):
    def test_familiarity_never_reaches_gem(self):
        expected = {
            10: "taxi",
            9: "taxi",
            8: "climb",
            7: "climb",
            6: "burn",
            5: "burn",
            4: "stall",
            3: "stall",
            2: "apogee",
            1: "apogee",
        }
        for score, tier in expected.items():
            self.assertEqual(tier_for_familiarity(score), tier)
        self.assertEqual(tier_for_familiarity(0), "apogee")
        self.assertEqual(tier_for_familiarity(40), "taxi")
        for score in range(1, 11):
            self.assertNotEqual(tier_for_familiarity(score), "escape")

    def test_rarity_cuts_cover_the_common_end(self):
        self.assertEqual(tier_for_rarity(0), "taxi")
        self.assertEqual(tier_for_rarity(0.1), "climb")
        self.assertEqual(tier_for_rarity(0.2), "burn")
        self.assertEqual(tier_for_rarity(0.4), "stall")
        self.assertEqual(tier_for_rarity(0.8), "apogee")
        self.assertEqual(tier_for_rarity(0.999), "escape")

    def test_most_of_a_long_list_is_in_the_deeper_tiers(self):
        answers = [
            {"name": f"Answer {index:04d}", "aliases": [], "pop": 1000 - index, "sitelinks": max(1, 400 - index)}
            for index in range(200)
        ]
        ranked = assign_by_popularity(answers)
        deep = sum(1 for answer in ranked if answer["tier"] in {"stall", "apogee", "escape"})
        self.assertGreater(deep, len(ranked) / 2)

    def test_popularity_assignment_has_one_recognizable_gem(self):
        answers = []
        for index in range(48):
            sitelinks = 120 - index * 2
            answers.append(
                {
                    "name": f"Answer {index:02d}",
                    "aliases": [],
                    "pop": sitelinks,
                    "sitelinks": sitelinks,
                }
            )
        # A junk tail that is rarer than the recognizable band.
        answers.append({"name": "Obscure Junk", "aliases": [], "pop": 3, "sitelinks": 4})
        ranked = assign_by_popularity(answers)
        gems = [answer for answer in ranked if answer["gem"]]
        self.assertEqual(len(gems), 1)
        self.assertEqual(gems[0]["tier"], "escape")
        self.assertGreaterEqual(gems[0]["sitelinks"], 8)
        self.assertNotEqual(gems[0]["name"], "Answer 00")
        self.assertNotEqual(gems[0]["name"], "Obscure Junk")
        tiers = {answer["tier"] for answer in ranked}
        self.assertEqual(tiers, {"taxi", "climb", "burn", "stall", "apogee", "escape"})
        self.assertEqual(sum(1 for answer in ranked if answer["tier"] == "escape"), 1)
        self.assertEqual(ranked[0]["tier"], "taxi")

    def test_ordered_curated_list_forces_the_named_gem(self):
        entries = [{"name": f"Item {i}", "aliases": []} for i in range(46)]
        entries[40] = {"name": "Dry Tortugas", "aliases": ["dry tortugas national park"]}
        answers = assign_ordered(entries, "Dry Tortugas")
        gems = [answer for answer in answers if answer["gem"]]
        self.assertEqual(gems[0]["name"], "Dry Tortugas")
        self.assertEqual(gems[0]["tier"], "escape")
        self.assertEqual(allocate(45), [9, 10, 10, 8, 8])
        counts = {}
        for answer in answers:
            counts[answer["tier"]] = counts.get(answer["tier"], 0) + 1
        self.assertEqual(counts["escape"], 1)
        for tier in ("taxi", "climb", "burn", "stall", "apogee"):
            self.assertGreaterEqual(counts[tier], 1)


if __name__ == "__main__":
    unittest.main()
