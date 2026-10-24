import unittest

from pipeline.curated import load_curated
from pipeline.quality import evaluate


class CuratedTests(unittest.TestCase):
    def test_hand_prompts_pass_the_gates(self):
        prompts = load_curated()
        self.assertGreaterEqual(len(prompts), 30)
        for prompt in prompts:
            self.assertEqual(evaluate(prompt), [], prompt["id"])
            self.assertEqual(prompt["source"], "hand")
            gems = [row for row in prompt["answers"] if row["gem"]]
            self.assertEqual(len(gems), 1)
            self.assertEqual(gems[0]["tier"], "apex")


if __name__ == "__main__":
    unittest.main()
