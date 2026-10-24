import assert from "node:assert/strict";
import { readFile, stat } from "node:fs/promises";
import test from "node:test";

import { compileAnswers } from "../js/match.js";
import { dailyPromptIds, utcDate } from "../js/select.js";

const TIERS = ["taxi", "climb", "burn", "stall", "apogee", "escape"];

test("published bank clears the seed bar", async () => {
  const index = JSON.parse(await readFile(new URL("../data/index.json", import.meta.url), "utf8"));
  assert.equal(index.version >= 5, true);
  const ids = [];
  const counts = [];
  let curated = 0;
  let wikidata = 0;
  let answers = 0;
  const yearId = /^wd-(?:film|album|game|tv|tvuk|song|book)-\d{4}$/;
  const yearText = /\b(?:1[89]\d{2}|20\d{2})\b/;
  for (const shard of index.shards) {
    const file = new URL(`../${shard.file}`, import.meta.url);
    const info = await stat(file);
    assert.ok(info.size < 2 * 1024 * 1024, `${shard.file} is ${info.size} bytes`);
    const prompts = JSON.parse(await readFile(file, "utf8"));
    assert.equal(prompts.length, shard.count, shard.file);
    assert.deepEqual(prompts.map((prompt) => prompt.id), shard.ids, shard.file);
    for (const prompt of prompts) {
      ids.push(prompt.id);
      counts.push(prompt.answers.length);
      assert.equal(yearId.test(prompt.id), false, prompt.id);
      assert.equal(yearText.test(prompt.text), false, prompt.text);
      if (prompt.source === "curated") curated += 1;
      if (prompt.source === "wikidata") wikidata += 1;
      assert.ok(prompt.answers.length >= 30, `${prompt.id} ${prompt.answers.length}`);
      assert.match(prompt.text, /^Name an? /);
      const gems = prompt.answers.filter((answer) => answer.gem);
      assert.equal(gems.length, 1, prompt.id);
      assert.equal(gems[0].tier, "escape", prompt.id);
      for (const tier of TIERS) {
        assert.ok(prompt.answers.some((answer) => answer.tier === tier), `${prompt.id} ${tier}`);
      }
      const compiled = compileAnswers(prompt.answers);
      for (const [key, value] of compiled.exact) {
        assert.ok(value, `${prompt.id} collision on ${key}`);
      }
      answers += prompt.answers.length;
    }
  }
  assert.equal(new Set(ids).size, ids.length);
  assert.equal(ids.length, index.promptCount);
  assert.equal(answers, index.answerCount);
  assert.ok(curated >= 40, curated);
  assert.ok(wikidata >= 100, wikidata);
  assert.ok(index.promptCount >= 160, `only ${index.promptCount} prompts`);
  for (const shard of index.shards) {
    assert.match(shard.file, /^data\/bank\/v\d+\//);
  }
  counts.sort((a, b) => a - b);
  const median = counts[Math.floor(counts.length / 2)];
  assert.ok(median >= 180, `median ${median}`);
  assert.ok(counts[0] >= 30, `min ${counts[0]}`);
  const daily = dailyPromptIds(ids, utcDate(), 7);
  assert.equal(daily.length, 7);
  assert.equal(new Set(daily).size, 7);

  const banned = [
    "wd-gk-castle-ir",
    "wd-gk-club-hu",
    "wd-gk-lang-in",
    "wd-gk-cricket-pk",
    "wd-alps",
    "wd-opera",
    "wd-kpop",
    "cur-language",
    "cur-phobia",
    "cur-constellation",
    "cur-unit",
    "cur-moon",
    "wd-gk-alkaloid",
  ];
  for (const id of banned) assert.equal(ids.includes(id), false, id);
  const loaded = new Map();
  for (const shard of index.shards) {
    const prompts = JSON.parse(await readFile(new URL(`../${shard.file}`, import.meta.url), "utf8"));
    for (const prompt of prompts) loaded.set(prompt.id, prompt);
  }
  const texts = [...loaded.values()].map((prompt) => prompt.text);
  const bannedText = [
    /in Iran/i,
    /Hungarian/i,
    /language of India/i,
    /K-pop/i,
    /cricketer/i,
    /Bundesliga/i,
    /La Liga/i,
    /Serie A/i,
    /Ligue 1/i,
    /the Alps/i,
    /state park/i,
    /Name a phobia/i,
    /Name a constellation/i,
    /Name an alkaloid/i,
    /Shinto/i,
    /Roman god/i,
    /programming language/i,
  ];
  for (const pattern of bannedText) {
    const hit = texts.find((text) => pattern.test(text));
    assert.equal(hit, undefined, String(pattern));
  }
  const floors = {
    "cur-pokemon": 800,
    "cur-starwars": 200,
    "cur-potter": 120,
    "cur-simpsons": 150,
    "cur-game-char": 200,
    "cur-animated": 200,
    "cur-director": 400,
    "cur-tv": 400,
    "cur-channel": 40,
    "cur-cereal": 80,
    "cur-snack": 80,
    "cur-clothes-brand": 150,
    "cur-disney-char": 200,
    "cur-city-ca": 150,
  };
  for (const [id, floor] of Object.entries(floors)) {
    const prompt = loaded.get(id);
    assert.ok(prompt, id);
    assert.ok(prompt.answers.length >= floor, `${id} ${prompt.answers.length}`);
  }
  const tierOf = (id, name) => {
    const key = name.toLowerCase();
    const answer = loaded.get(id).answers.find((item) => item.name.toLowerCase() === key);
    return answer && answer.tier;
  };
  assert.equal(tierOf("cur-pokemon", "Pikachu"), "taxi");
  assert.equal(tierOf("cur-starwars", "Luke Skywalker"), "taxi");
  assert.equal(tierOf("cur-city-ca", "Los Angeles"), "taxi");
  assert.equal(loaded.get("cur-nfl").answers.length, 32);
  assert.equal(loaded.get("cur-nba").answers.length, 30);
  assert.equal(loaded.get("cur-mlb").answers.length, 30);
  assert.ok(loaded.get("cur-holiday").answers.length >= 30);
  assert.ok(loaded.get("cur-holiday").answers.length <= 80);
  assert.equal(loaded.get("wd-us-state").answers.length, 50);
  assert.equal(loaded.get("wd-president").answers.length, 51);
});
