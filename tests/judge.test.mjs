import assert from "node:assert/strict";
import test from "node:test";

import {
  allowRequest,
  cacheKey,
  judgeEndpoint,
  judgeMessages,
  parseVerdict,
  requestBody,
  scoreJudged,
  validAnswer,
} from "../netlify/lib/judge-core.js";

test("judge stays pointed at a token-checked proxy path", () => {
  assert.equal(judgeEndpoint(""), null);
  assert.deepEqual(judgeEndpoint("https://box.example/v1"), {
    mode: "openai",
    url: "https://box.example/v1/chat/completions",
  });
  assert.deepEqual(judgeEndpoint("https://box.example/api"), {
    mode: "ollama",
    url: "https://box.example/api/chat",
  });
  assert.equal(judgeEndpoint("http://127.0.0.1:11434").url, "http://127.0.0.1:11434/v1/chat/completions");
});

test("verdict JSON is strict enough to score, and junk is dropped", () => {
  const parsed = parseVerdict('```json\n{"valid": true, "canonical": "Lesotho", "familiarity": 6, "reason": "a country"}\n```');
  assert.equal(parsed.canonical, "Lesotho");
  assert.equal(parsed.familiarity, 6);
  assert.equal(parseVerdict("nope"), null);
  assert.equal(parseVerdict('{"valid": true, "canonical": "x", "familiarity": "many"}'), null);
  assert.equal(validAnswer("  paris "), "paris");
  assert.equal(validAnswer("x".repeat(61)), "");
  assert.equal(validAnswer("shit"), "");
});

test("judged familiarity never reaches the gem, and a bank hit keeps it", () => {
  const scored = scoreJudged(
    { valid: true, canonical: "Lesotho", familiarity: 1, reason: "rare" },
    null,
  );
  assert.equal(scored.judged, true);
  assert.equal(scored.tier, "apogee");
  assert.equal(scored.gem, false);
  assert.equal(scored.points, 60);
  const bank = scoreJudged(null, { name: "Lesotho", tier: "escape", gem: true });
  assert.equal(bank.judged, false);
  assert.equal(bank.inBank, true);
  assert.equal(bank.tier, "escape");
  assert.equal(bank.points, 100);
  assert.equal(scoreJudged({ valid: false, canonical: "", familiarity: 1, reason: "no" }, null).valid, false);
});

test("cache key and rate limit", () => {
  assert.equal(cacheKey("wd-country", "The Lesotho"), "wd-country__lesotho");
  const first = allowRequest([], 1000, 2, 500);
  const second = allowRequest(first.hits, 1100, 2, 500);
  const third = allowRequest(second.hits, 1200, 2, 500);
  assert.equal(first.ok, true);
  assert.equal(second.ok, true);
  assert.equal(third.ok, false);
  const later = allowRequest(third.hits, 2000, 2, 500);
  assert.equal(later.ok, true);
});

test("obscure real members stay valid and familiarity is separate", () => {
  const text = judgeMessages("Name a city in Oregon", "Joseph")
    .map((message) => message.content)
    .join("\n");
  assert.match(text, /separately/);
  assert.match(text, /Not being famous does not make it invalid/);
  assert.match(text, /Joseph is valid with familiarity 1 or 2/);
  assert.match(text, /Portland is valid with familiarity 9 or 10/);
  assert.doesNotMatch(text, /valid is true only when/);
});

test("upstream body asks for JSON and disables thinking", () => {
  const body = requestBody("ollama", "qwen3.8:27b", []);
  assert.equal(body.think, false);
  assert.equal(body.stream, false);
  assert.equal(body.format.required.includes("familiarity"), true);
  const openai = requestBody("openai", "qwen3.8:27b", []);
  assert.equal(openai.temperature, 0.1);
  assert.equal(openai.response_format.json_schema.schema.required.includes("valid"), true);
});
