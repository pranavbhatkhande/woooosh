"""LLM idea filters, JSON repair, and percentile tiering. No network."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pipeline import llm
from pipeline.llm import (
    _build,
    _payload,
    _tier_rows,
    chat_json,
    content_words,
    filter_ideas,
    overlaps,
    parse_json_lenient,
    too_small,
)


class LlmTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_raw = llm.RAW
        llm.RAW = Path(self.tmp.name)

    def tearDown(self) -> None:
        llm.RAW = self.old_raw
        self.tmp.cleanup()

    def test_trailing_comma_and_fence_parse(self) -> None:
        text = '```json\n{"answers": [{"name": "Oak",}]}\n```'
        data = parse_json_lenient(text)
        self.assertEqual(data["answers"][0]["name"], "Oak")

    def test_tiny_planets_drop_and_ocean_liner_stays(self) -> None:
        self.assertTrue(too_small("Name a planet in our solar system"))
        self.assertFalse(too_small("Name an ocean liner"))
        self.assertIn("liner", content_words("Name an ocean liner"))

    def test_overlap_rejects_another_pasta_prompt(self) -> None:
        existing = [set(content_words("Name a pasta shape"))]
        self.assertTrue(overlaps("Name a type of pasta", existing))
        self.assertFalse(overlaps("Name an ocean liner", existing))

    def test_filter_reports_counts(self) -> None:
        ideas = [
            {"text": "Name a planet in our solar system", "category": "space"},
            {"text": "Name a pasta shape", "category": "food"},
            {"text": "Name a roofing material", "category": "building"},
        ]
        kept, reasons = filter_ideas(
            ideas,
            {"name a pasta shape"},
            [set(content_words("Name a pasta shape"))],
        )
        self.assertEqual([idea["text"] for idea in kept], ["Name a roofing material"])
        self.assertEqual(reasons["tiny"], 1)
        self.assertEqual(reasons["duplicate"], 1)

    def test_flat_familiarity_still_fills_every_tier(self) -> None:
        rows = [{"name": f"Herb {index:02d}", "aliases": [], "familiarity": 7} for index in range(48)]
        tiered = _tier_rows(rows)
        self.assertIsNotNone(tiered)
        tiers = {answer["tier"] for answer in tiered}
        self.assertEqual(tiers, {"taxi", "climb", "burn", "stall", "apogee", "escape"})
        deep = sum(1 for answer in tiered if answer["tier"] in {"stall", "apogee", "escape"})
        self.assertGreater(deep, len(tiered) / 2)

    def test_ollama_format_is_the_schema_object(self) -> None:
        schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}
        body = _payload("ollama", "qwen", [], schema, 128)
        self.assertIs(body["format"], schema)
        self.assertFalse(body["think"])

    def test_bad_json_retries_and_a_failed_cache_is_not_a_hit(self) -> None:
        calls = {"n": 0}

        def fake_post(body, timeout):
            calls["n"] += 1
            if calls["n"] == 1:
                return "nope"
            return '{"ok": true}'

        with mock.patch("pipeline.llm._post", side_effect=fake_post):
            first = chat_json([{"role": "user", "content": "go"}], schema={"type": "object"})
        self.assertEqual(first, {"ok": True})
        self.assertEqual(calls["n"], 2)
        with mock.patch("pipeline.llm._post", side_effect=AssertionError("network")):
            second = chat_json([{"role": "user", "content": "go"}], schema={"type": "object"})
        self.assertEqual(second, {"ok": True})

    def test_build_accepts_a_flat_list(self) -> None:
        names = [f"Herb {index:02d}" for index in range(45)]

        def fake_chat(messages, schema=None, timeout=180, num_predict=4096):
            content = messages[-1]["content"]
            if "Keep only names" in content:
                return {"keep": names}
            return {
                "answers": [{"name": name, "aliases": [], "familiarity": 7} for name in names],
            }

        with mock.patch("pipeline.llm.chat_json", side_effect=fake_chat):
            prompt = _build({"text": "Name a dried herb", "category": "food"}, set())
        self.assertIsNotNone(prompt)
        self.assertGreaterEqual(len(prompt["answers"]), 40)
        self.assertEqual(sum(1 for answer in prompt["answers"] if answer["gem"]), 1)


if __name__ == "__main__":
    unittest.main()
