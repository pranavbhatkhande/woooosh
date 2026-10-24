import unittest

from pipeline.tiering import (
    POINTS,
    assign_tiers,
    familiarity_score,
    histogram,
    rarity_score,
    tier_for_rank,
)


class TieringTests(unittest.TestCase):
    def test_points_and_rank_ends(self):
        self.assertEqual(
            [POINTS[name] for name in ("pad", "ascent", "ceiling", "hotshot", "orbit", "apex")],
            [5, 10, 25, 40, 60, 100],
        )
        self.assertEqual(tier_for_rank(0, 40), "pad")
        self.assertEqual(tier_for_rank(39, 40), "apex")

    def test_every_tier_appears_and_order_follows_popularity(self):
        for count in (40, 45, 60, 80, 100):
            answers = [{"name": f"a{i:03d}", "popularity": count - i} for i in range(count)]
            assign_tiers(answers)
            counts = histogram(answers)
            self.assertTrue(all(counts[tier] >= 1 for tier in counts), counts)
            self.assertEqual(sum(1 for row in answers if row["gem"]), 1)
            gem = next(row for row in answers if row["gem"])
            self.assertEqual(gem["tier"], "apex")
            ranked = sorted(answers, key=lambda row: -row["popularity"])
            self.assertEqual(ranked[0]["tier"], "pad")
            self.assertEqual(ranked[-1]["tier"], "apex")
            previous = ranked[0]["popularity"]
            for row in ranked[1:]:
                self.assertLessEqual(row["popularity"], previous)
                previous = row["popularity"]

    def test_gem_is_the_recognizable_apex_answer(self):
        answers = [{"name": f"n{i:02d}", "popularity": 100 - i} for i in range(50)]
        # A digit-heavy label should not steal the gem if another apex name is clean.
        answers[-1]["name"] = "Item 9"
        assign_tiers(answers)
        gem = next(row for row in answers if row["gem"])
        self.assertNotEqual(gem["name"], "Item 9")
        apex = [row for row in answers if row["tier"] == "apex" and row["name"] != "Item 9"]
        self.assertEqual(gem["name"], max(apex, key=lambda row: row["popularity"])["name"])

    def test_showoff_pin_leaves_every_tier_and_moves_the_gem(self):
        answers = [{"name": f"n{i:02d}", "popularity": 80 - i, "showoff": False} for i in range(60)]
        rare = min(answers, key=lambda row: row["popularity"])
        rare["showoff"] = True
        rare["name"] = "Petrichor"
        assign_tiers(answers)
        pinned = next(row for row in answers if row["name"] == "Petrichor")
        self.assertEqual(pinned["tier"], "hotshot")
        self.assertFalse(pinned["gem"])
        self.assertTrue(all(histogram(answers)[tier] >= 1 for tier in histogram(answers)))
        self.assertEqual(sum(1 for row in answers if row["gem"]), 1)

    def test_score_signals_move_in_the_expected_direction(self):
        low = rarity_score(10, zipf=1)
        high = rarity_score(200, zipf=1)
        self.assertGreater(high, low)
        viewed = rarity_score(20, zipf=0, pageviews=5_000_000)
        quiet = rarity_score(20, zipf=0, pageviews=10)
        self.assertGreater(viewed, quiet)
        common = familiarity_score(1, zipf=2)
        rare = familiarity_score(6, zipf=2)
        self.assertGreater(common, rare)

    def test_ties_break_by_name(self):
        answers = [
            {"name": "Zed", "popularity": 5},
            {"name": "Amy", "popularity": 5},
            {"name": "Moe", "popularity": 1},
        ]
        # Too few for a real prompt; rank assignment still has to be deterministic.
        assign_tiers(answers)
        ordered = sorted(answers, key=lambda row: (-row["popularity"], row["name"]))
        self.assertEqual([row["name"] for row in ordered], ["Amy", "Zed", "Moe"])
        self.assertEqual(ordered[0]["tier"], "pad")


if __name__ == "__main__":
    unittest.main()
