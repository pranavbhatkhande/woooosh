import assert from "node:assert/strict";
import test from "node:test";
import { PLAY_MS, PREVIEW_MS, RUN_LENGTH } from "../js/constants.js";
import {
  advance,
  entryBlurb,
  nextPrompt,
  passPrompt,
  sampleOthers,
  shareText,
  startRun,
  submitAnswer,
  totalKm,
} from "../js/engine.js";
import { zoneFor } from "../js/tiers.js";
import { recordResult } from "../js/storage.js";
import { fallbackDailyIds, idsForDate, shiftDate } from "../js/daily.js";
import { createDeck, takeRun } from "../js/deck.js";

function prompt(id, answers) {
  return { id, text: `Name ${id}`, answers };
}

const sampleAnswers = [
  { name: "Oxygen", aliases: ["O2"], tier: "pad", gem: false },
  { name: "Iron", aliases: [], tier: "ascent", gem: false },
  { name: "Copper", aliases: [], tier: "ceiling", gem: false },
  { name: "Bismuth", aliases: [], tier: "hotshot", gem: false },
  { name: "Tellurium", aliases: [], tier: "orbit", gem: false },
  { name: "Tennessine", aliases: [], tier: "apex", gem: true },
];

function seven() {
  return Array.from({ length: RUN_LENGTH }, (_, i) => prompt(`p${i}`, sampleAnswers));
}

test("preview blocks answers, then the window opens", () => {
  const now = 1_000;
  let run = startRun({ prompts: seven(), mode: "daily", date: "2026-10-24", now });
  assert.equal(run.phase, "preview");
  assert.equal(run.entries.length, 7);
  assert.equal(submitAnswer(run, "Oxygen", now).reason, "closed");
  run = advance(run, now + PREVIEW_MS - 1);
  assert.equal(run.phase, "preview");
  run = advance(run, now + PREVIEW_MS);
  assert.equal(run.phase, "play");
  assert.equal(run.phaseEndsAt, now + PREVIEW_MS + PLAY_MS);
});

test("a miss does not score or advance, and the first hit locks", () => {
  let run = startRun({ prompts: seven(), mode: "unlimited", now: 0 });
  run = advance(run, PREVIEW_MS);
  const missed = submitAnswer(run, "unobtainium", PREVIEW_MS + 10);
  assert.equal(missed.reason, "miss");
  assert.equal(missed.run.index, 0);
  assert.equal(missed.run.phase, "play");
  assert.equal(totalKm(missed.run), 0);
  const hit = submitAnswer(missed.run, "bismuth", PREVIEW_MS + 20);
  assert.equal(hit.accepted, true);
  assert.equal(hit.run.entries[0].answer.tier, "hotshot");
  assert.equal(hit.run.entries[0].answer.points, 40);
  assert.match(entryBlurb(hit.run.entries[0]), /not actually rare/i);
  const again = submitAnswer(hit.run, "Oxygen", PREVIEW_MS + 30);
  assert.equal(again.reason, "closed");
  assert.equal(again.run.entries[0].answer.name, "Bismuth");
});

test("pass and timeout score zero and the run still has seven prompts", () => {
  let run = startRun({ prompts: seven(), mode: "daily", date: "2026-10-24", now: 0 });
  run = advance(run, PREVIEW_MS);
  run = passPrompt(run, PREVIEW_MS + 5).run;
  assert.equal(run.entries[0].outcome, "pass");
  assert.equal(run.entries[0].answer, null);
  run = nextPrompt(run, 5_000);
  assert.equal(run.phase, "preview");
  assert.equal(run.index, 1);
  run = advance(run, 5_000 + PREVIEW_MS);
  run = advance(run, run.phaseEndsAt);
  assert.equal(run.entries[1].outcome, "timeout");
  assert.equal(totalKm(run), 0);
  for (let i = 2; i < 7; i += 1) {
    run = nextPrompt(run, 10_000 + i);
    run = advance(run, run.phaseEndsAt);
    run = submitAnswer(run, "Tennessine", run.phaseEndsAt - 1).run;
  }
  run = nextPrompt(run, 20_000);
  assert.equal(run.phase, "done");
  assert.equal(run.entries.length, 7);
  assert.equal(totalKm(run), 5 * 100);
  const text = shareText(run, "https://woooosh.ai");
  const lines = text.split("\n");
  assert.equal([...lines[1]].length, 7);
  assert.match(text, /500 km/);
  assert.match(text, /High Orbit/);
  assert.match(text, /2026-10-24/);
});

test("zones follow altitude", () => {
  assert.equal(zoneFor(0).label, "The Pad");
  assert.equal(zoneFor(1).label, "Troposphere");
  assert.equal(zoneFor(11).label, "Troposphere");
  assert.equal(zoneFor(12).label, "Stratosphere");
  assert.equal(zoneFor(35).label, "Stratosphere");
  assert.equal(zoneFor(50).label, "Mesosphere");
  assert.equal(zoneFor(80).label, "Kármán Edge");
  assert.equal(zoneFor(100).label, "Thermosphere");
  assert.equal(zoneFor(200).label, "Low Orbit");
  assert.equal(zoneFor(350).label, "High Orbit");
  assert.equal(zoneFor(550).label, "Deep Black");
  assert.equal(zoneFor(700).label, "Deep Black");
});

test("sample answers cover other tiers and the gem", () => {
  const examples = sampleOthers({ answers: sampleAnswers }, "Oxygen");
  assert.equal(examples.some((answer) => answer.gem), true);
  assert.equal(examples.some((answer) => answer.name === "Oxygen"), false);
  assert.ok(examples.length >= 4);
});

test("daily ids are stable, scheduled dates win, and streaks continue", () => {
  const ids = ["b", "a", "c", "d", "e", "f", "g", "h", "i"];
  const first = fallbackDailyIds(ids, "2026-10-24");
  const again = fallbackDailyIds(["i", "h", "a", "b", "c", "d", "e", "f", "g"], "2026-10-24");
  assert.deepEqual(first, again);
  assert.equal(new Set(first).size, 7);
  assert.notDeepEqual(first, fallbackDailyIds(ids, "2026-10-25"));
  const scheduled = ["a", "b", "c", "d", "e", "f", "g"];
  assert.deepEqual(idsForDate({ dates: { "2026-10-24": scheduled } }, ids, "2026-10-24"), scheduled);

  let stats = recordResult({ streak: 0, bestStreak: 0, lastDaily: null, bestKm: 0, runs: 0 }, {
    mode: "daily", date: "2026-10-23", km: 40,
  });
  stats = recordResult(stats, { mode: "daily", date: "2026-10-24", km: 80 });
  assert.equal(stats.streak, 2);
  assert.equal(stats.bestKm, 80);
  const repeat = recordResult(stats, { mode: "daily", date: "2026-10-24", km: 10 });
  assert.equal(repeat.streak, 2);
  assert.equal(repeat.runs, 2);
  const gap = recordResult(stats, { mode: "daily", date: shiftDate("2026-10-24", 2), km: 5 });
  assert.equal(gap.streak, 1);
});

test("unlimited does not repeat until the bank is exhausted, then oldest first", () => {
  const ids = ["a", "b", "c", "d"];
  let deck = { seenOrder: [], remaining: ["a", "b", "c", "d"], cycle: 1 };
  const first = takeRun(deck, ids, 3, () => 0);
  assert.deepEqual(first.ids, ["a", "b", "c"]);
  const second = takeRun(first.deck, ids, 3, () => 0);
  assert.deepEqual(second.ids, ["d", "a", "b"]);
  assert.equal(new Set(first.ids.concat(second.ids.slice(0, 1))).size, 4);
  const grown = takeRun(first.deck, ["a", "b", "c", "d", "e"], 2, () => 0);
  assert.equal(grown.ids[0], "e");
  const fresh = createDeck(["a", "b"], () => 0.5);
  assert.equal(fresh.remaining.length, 2);
});
