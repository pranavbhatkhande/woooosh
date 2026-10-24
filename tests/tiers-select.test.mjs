import assert from "node:assert/strict";
import test from "node:test";
import { nextPrompt, passPrompt, secondsLeft, startRun, tick, lockAnswer } from "../js/engine.js";
import { dailyPromptIds, planUnlimited, previousUtcDate } from "../js/select.js";
import { shareText } from "../js/share.js";
import { pointsFor, tierForFamiliarity, zoneFor } from "../js/tiers.js";

test("familiarity never awards the gem tier", () => {
  const expected = {
    10: "taxi",
    9: "taxi",
    8: "climb",
    7: "climb",
    6: "burn",
    5: "burn",
    4: "stall",
    3: "stall",
    2: "apogee",
    1: "apogee",
  };
  for (const [score, tier] of Object.entries(expected)) {
    assert.equal(tierForFamiliarity(Number(score)), tier);
  }
  assert.equal(tierForFamiliarity(0), "apogee");
  assert.equal(tierForFamiliarity(99), "taxi");
  assert.equal(tierForFamiliarity("nope"), null);
  for (let n = 1; n <= 10; n += 1) assert.notEqual(tierForFamiliarity(n), "escape");
  assert.equal(pointsFor("stall"), 40);
  assert.equal(pointsFor("escape"), 100);
});

test("zones follow altitude", () => {
  assert.equal(zoneFor(0).label, "THE PAD");
  assert.equal(zoneFor(11).label, "TROPOSPHERE");
  assert.equal(zoneFor(12).label, "STRATOSPHERE");
  assert.equal(zoneFor(100).label, "THERMOSPHERE");
  assert.equal(zoneFor(400).label, "HIGH ORBIT");
  assert.equal(zoneFor(700).label, "DEEP SPACE");
});

test("daily selection is stable and order-independent", () => {
  const ids = Array.from({ length: 40 }, (_, i) => `p${i}`);
  const a = dailyPromptIds(ids, "2026-10-24");
  const b = dailyPromptIds([...ids].reverse(), "2026-10-24");
  assert.deepEqual(a, b);
  assert.equal(a.length, 7);
  assert.equal(new Set(a).size, 7);
  const other = dailyPromptIds(ids, "2026-10-25");
  assert.notDeepEqual(a, other);
  assert.equal(previousUtcDate("2026-10-24"), "2026-10-23");
  assert.equal(previousUtcDate("2026-03-01"), "2026-02-28");
});

test("unlimited deck does not repeat until everything is seen, then oldest first", () => {
  const ids = ["a", "b", "c", "d"];
  let seen = {};
  let deck = [];
  const taken = [];
  for (let i = 0; i < 4; i += 1) {
    const plan = planUnlimited(ids, { seen, deck, seed: 7 });
    deck = plan.deck;
    taken.push(plan.id);
    seen = { ...seen, [plan.id]: 1000 + i };
    deck = deck.filter((id) => id !== plan.id);
  }
  assert.deepEqual(new Set(taken), new Set(ids));
  const again = planUnlimited(ids, { seen, deck, seed: 7 });
  const oldest = Object.entries(seen).sort((x, y) => x[1] - y[1])[0][0];
  assert.equal(again.id, oldest);
});

test("a run is seven locks, misses score zero, and the share grid matches", () => {
  const prompts = Array.from({ length: 7 }, (_, i) => ({
    id: `p${i}`,
    text: `Name a thing ${i}`,
    answers: [
      { name: "Alpha", tier: "taxi", gem: false },
      { name: "Zed", tier: "escape", gem: true },
    ],
  }));
  let now = 1_000;
  let state = startRun({ mode: "daily", date: "2026-10-24", prompts, now });
  assert.equal(state.phase, "preview");
  state = tick(state, now + 2000);
  assert.equal(state.phase, "play");
  assert.equal(secondsLeft(state, now + 2000), 25);
  state = lockAnswer(state, now + 3000, { name: "Alpha", tier: "taxi", typed: "alpha" });
  assert.equal(state.phase, "reveal");
  assert.equal(state.altitude, 5);
  state = nextPrompt(state, now + 4000);
  state = tick(state, state.phaseEndsAt);
  state = passPrompt(state, state.phaseEndsAt - 10);
  assert.equal(state.rounds.at(-1).kind, "pass");
  assert.equal(state.altitude, 5);
  while (state.phase !== "done") {
    if (state.phase === "preview") state = tick(state, state.phaseEndsAt);
    else if (state.phase === "play") state = tick(state, state.phaseEndsAt);
    else state = nextPrompt(state, state.phaseEndsAt + 1);
  }
  assert.equal(state.rounds.length, 7);
  const text = shareText({
    mode: "daily",
    date: "2026-10-24",
    altitude: state.altitude,
    zone: "TROPOSPHERE",
    rounds: state.rounds,
  });
  assert.match(text, /^WOOOOSH · DAILY · 2026-10-24/);
  assert.ok(text.includes("⬜"));
  assert.ok(text.includes("⬛"));
  assert.ok(text.endsWith("woooosh.ai"));
});
