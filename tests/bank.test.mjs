import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import { compileAnswers } from "../js/match.js";
import { dailyPromptIds, utcDate } from "../js/select.js";

const TIERS = ["taxi", "climb", "burn", "stall", "apogee", "escape"];

test("published bank clears the seed bar", async () => {
  const index = JSON.parse(await readFile(new URL("../data/index.json", import.meta.url), "utf8"));
  assert.ok(index.promptCount >= 200, `only ${index.promptCount} prompts`);
  assert.equal(index.version >= 1, true);
  const ids = [];
  let curated = 0;
  let wikidata = 0;
  let answers = 0;
  for (const shard of index.shards) {
    const prompts = JSON.parse(await readFile(new URL(`../${shard.file}`, import.meta.url), "utf8"));
    assert.equal(prompts.length, shard.count, shard.file);
    assert.deepEqual(prompts.map((prompt) => prompt.id), shard.ids, shard.file);
    for (const prompt of prompts) {
      ids.push(prompt.id);
      if (prompt.source === "curated") curated += 1;
      if (prompt.source === "wikidata") wikidata += 1;
      assert.ok(prompt.answers.length >= 40, prompt.id);
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
  assert.ok(wikidata >= 150, wikidata);
  const daily = dailyPromptIds(ids, utcDate(), 7);
  assert.equal(daily.length, 7);
  assert.equal(new Set(daily).size, 7);
});
