import unittest

from pipeline.normalize import candidates, normalize, within_one_edit


class NormalizeTests(unittest.TestCase):
    def test_folds_like_the_game(self):
        self.assertEqual(normalize("  The MATRIX! "), "matrix")
        self.assertEqual(normalize("Áustria"), "austria")
        self.assertEqual(normalize("rock & roll"), "rock and roll")
        self.assertEqual(normalize("Côte d'Ivoire"), "cote divoire")
        self.assertEqual(normalize("an atlas"), "atlas")

    def test_simple_plurals_and_the_paris_guard(self):
        self.assertIn("cat", candidates("cats"))
        self.assertIn("country", candidates("countries"))
        self.assertIn("berry", candidates("berries"))
        self.assertIn("bus", candidates("buses"))
        self.assertIn("movie", candidates("movies"))
        self.assertIn("horse", candidates("horses"))
        self.assertNotIn("pari", candidates("paris"))
        self.assertTrue(within_one_edit("austria", "austrai"))
        self.assertTrue(within_one_edit("gambia", "zambia"))
        self.assertFalse(within_one_edit("austria", "australia"))


if __name__ == "__main__":
    unittest.main()
