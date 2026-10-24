import unittest

from pipeline.publish import merge_prompts, shard_prompts
from pipeline.schedule import extend_schedule, pick_ids


class PublishTests(unittest.TestCase):
    def test_later_sources_override_and_ids_stay_sorted(self):
        merged = merge_prompts(
            [{"id": "b", "text": "old"}, {"id": "a", "text": "keep"}],
            [{"id": "b", "text": "generated"}],
            [{"id": "c", "text": "hand"}, {"id": "b", "text": "hand wins"}],
        )
        self.assertEqual([row["id"] for row in merged], ["a", "b", "c"])
        self.assertEqual(merged[1]["text"], "hand wins")

    def test_shards_cover_every_prompt(self):
        prompts = [{"id": f"p{i}"} for i in range(25)]
        shards = shard_prompts(prompts, 20)
        self.assertEqual([len(shard) for shard in shards], [20, 5])

    def test_daily_dates_do_not_move_once_pinned(self):
        ids = [f"p{i}" for i in range(12)]
        first = extend_schedule({}, ids, "2026-10-24", days=3, keep_past=0)
        pinned = list(first["2026-10-24"])
        grown = extend_schedule(first, ids + ["extra"], "2026-10-24", days=4, keep_past=0)
        self.assertEqual(grown["2026-10-24"], pinned)
        self.assertEqual(len(grown["2026-10-27"]), 7)
        self.assertEqual(len(set(pick_ids(ids, "2026-10-24"))), 7)


if __name__ == "__main__":
    unittest.main()
