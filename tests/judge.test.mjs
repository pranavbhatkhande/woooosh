import assert from "node:assert/strict";
import test from "node:test";

import { classifyJudgeResponse } from "../js/judge-client.js";
import { compileAnswers } from "../js/match.js";
import { scoreAttempt } from "../js/scoring.js";
import {
  allowRequest,
  cacheKey,
  judgeEndpoint,
  judgeMessages,
  parseVerdict,
  referenceEntries,
  requestBody,
  scoreJudged,
  settleJudged,
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

test("the judge enables when JUDGE_URL is set, and an exact bank hit skips the model", async () => {
  const { handler } = await import("../netlify/functions/judge.js");
  const previous = process.env.JUDGE_URL;
  delete process.env.JUDGE_URL;
  try {
    const off = await handler({ httpMethod: "GET", headers: {} });
    assert.equal(JSON.parse(off.body).enabled, false);
    process.env.JUDGE_URL = "https://example.invalid/api";
    const on = await handler({ httpMethod: "GET", headers: {} });
    assert.equal(JSON.parse(on.body).enabled, true);
    let calls = 0;
    const prev = globalThis.fetch;
    globalThis.fetch = async (...args) => {
      calls += 1;
      return prev(...args);
    };
    try {
      const post = await handler({
        httpMethod: "POST",
        headers: { host: "example.test" },
        body: JSON.stringify({ promptId: "wd-country", answer: "France" }),
      });
      assert.equal(post.statusCode, 200);
      const data = JSON.parse(post.body);
      assert.equal(data.enabled, true);
      assert.equal(data.valid, true);
      assert.equal(data.inBank, true);
      assert.equal(data.canonical, "France");
      assert.equal(data.judged, false);
      assert.equal(calls, 0);
    } finally {
      globalThis.fetch = prev;
    }
  } finally {
    if (previous === undefined) delete process.env.JUDGE_URL;
    else process.env.JUDGE_URL = previous;
  }
});

test("upstream body asks for JSON and disables thinking", () => {
  const body = requestBody("ollama", "qwen3.8:27b", []);
  assert.equal(body.think, false);
  assert.equal(body.stream, false);
  assert.equal(body.keep_alive, "30m");
  assert.equal(body.format.required.includes("familiarity"), true);
  const openai = requestBody("openai", "qwen3.8:27b", []);
  assert.equal(openai.temperature, 0.1);
  assert.equal(openai.keep_alive, undefined);
  assert.equal(openai.response_format.json_schema.schema.required.includes("valid"), true);
});

const cities = compileAnswers([
  { name: "Portland", aliases: [], tier: "taxi", gem: false },
  { name: "Salem", aliases: [], tier: "climb", gem: false },
  { name: "Eugene", aliases: [], tier: "climb", gem: false },
  { name: "Joseph", aliases: [], tier: "burn", gem: false },
]);

test("scoring: exact bank hit, typo mapped to canonical, unlisted accept, reject, timeout fallback", () => {
  const exact = scoreAttempt(cities, "Portland", { status: "pending" });
  assert.equal(exact.action, "lock");
  assert.equal(exact.hit.name, "Portland");
  assert.equal(exact.hit.tier, "taxi");
  assert.equal(exact.hit.judged, false);

  const mapped = settleJudged(cities, "Portlnd", {
    valid: true,
    canonical: "Portland",
    familiarity: 10,
    reason: "typo",
  });
  assert.equal(mapped.valid, true);
  assert.equal(mapped.inBank, true);
  assert.equal(mapped.judged, false);
  assert.equal(mapped.canonical, "Portland");
  assert.equal(mapped.tier, "taxi");
  assert.equal(mapped.points, 5);
  const mappedClient = scoreAttempt(cities, "Portlnd", { status: "scored", data: mapped });
  assert.equal(mappedClient.action, "lock");
  assert.equal(mappedClient.hit.name, "Portland");
  assert.equal(mappedClient.hit.judged, false);

  const unlisted = settleJudged(cities, "Manzanita", {
    valid: true,
    canonical: "Manzanita",
    familiarity: 2,
    reason: "small Oregon city",
  });
  assert.equal(unlisted.valid, true);
  assert.equal(unlisted.inBank, false);
  assert.equal(unlisted.judged, true);
  assert.equal(unlisted.canonical, "Manzanita");
  assert.equal(unlisted.tier, "apogee");
  assert.equal(unlisted.gem, false);

  const rejected = settleJudged(cities, "Portlnd", {
    valid: false,
    canonical: "",
    familiarity: 1,
    reason: "not a city",
  });
  assert.equal(rejected.valid, false);
  const rejectedClient = scoreAttempt(cities, "Portlnd", { status: "reject" });
  assert.equal(rejectedClient.action, "shake");
  assert.equal(rejectedClient.remember, true);

  const timedOut = settleJudged(cities, "Portlnd", null);
  assert.equal(timedOut.valid, true);
  assert.equal(timedOut.canonical, "Portland");
  assert.equal(timedOut.tier, "taxi");
  assert.equal(timedOut.judged, false);
  const fallback = scoreAttempt(cities, "Portlnd", { status: "fallback" });
  assert.equal(fallback.action, "lock");
  assert.equal(fallback.hit.name, "Portland");
  assert.equal(fallback.hit.judged, false);
  assert.equal(scoreAttempt(cities, "zzzzqqqq", { status: "fallback" }).action, "shake");
});

test("near bank entries are the judge's lookup list", () => {
  const refs = referenceEntries(cities, "Portlnd");
  assert.equal(refs[0].name, "Portland");
  const clubs = compileAnswers([
    { name: "Paris Saint-Germain", aliases: [], tier: "taxi", gem: false },
    { name: "Marseille", aliases: [], tier: "climb", gem: false },
  ]);
  assert.equal(referenceEntries(clubs, "psg")[0].name, "Paris Saint-Germain");
  const text = judgeMessages("Name a city in Oregon", "Portlnd", refs)
    .map((message) => message.content)
    .join("\n");
  assert.match(text, /Reference entries:/);
  assert.match(text, /- Portland/);
  assert.match(text, /copied exactly/);
});

test("a judge transport failure falls back and a real reject does not", () => {
  assert.equal(classifyJudgeResponse(false, { enabled: true, error: "upstream" }).status, "fallback");
  assert.equal(classifyJudgeResponse(false, { enabled: true, error: "rate" }).status, "fallback");
  assert.equal(classifyJudgeResponse(true, { enabled: true, valid: false }).status, "reject");
  const scored = classifyJudgeResponse(true, {
    enabled: true,
    valid: true,
    tier: "taxi",
    canonical: "Portland",
    inBank: true,
  });
  assert.equal(scored.status, "scored");
  assert.equal(scored.data.canonical, "Portland");
});
