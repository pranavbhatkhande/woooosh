import assert from "node:assert/strict";
import { readFile, stat } from "node:fs/promises";
import test from "node:test";

import { compileAnswers } from "../js/match.js";
import { dailyPromptIds, utcDate } from "../js/select.js";

const TIERS = ["taxi", "climb", "burn", "stall", "apogee", "escape"];

test("published bank clears the seed bar", async () => {
  const index = JSON.parse(await readFile(new URL("../data/index.json", import.meta.url), "utf8"));
  assert.ok(index.promptCount >= 200, `only ${index.promptCount} prompts`);
  assert.equal(index.version >= 1, true);
  const ids = [];
  const counts = [];
  let curated = 0;
  let wikidata = 0;
  let answers = 0;
  let film2015 = 0;
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
      if (prompt.id === "wd-film-2015") film2015 = prompt.answers.length;
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
  assert.ok(curated >= 30, curated);
  assert.ok(wikidata >= 200, wikidata);
  counts.sort((a, b) => a - b);
  const median = counts[Math.floor(counts.length / 2)];
  assert.ok(median >= 400, `median ${median}`);
  assert.ok(film2015 >= 1000, `wd-film-2015 has ${film2015}`);
  const daily = dailyPromptIds(ids, utcDate(), 7);
  assert.equal(daily.length, 7);
  assert.equal(new Set(daily).size, 7);
});
