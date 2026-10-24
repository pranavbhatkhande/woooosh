import assert from "node:assert/strict";
import test from "node:test";
import {
  burstCount,
  burstShape,
  finalePops,
  flightLine,
  flightMood,
  peakTier,
  rocketProgress,
  scoreProgress,
  tierRung,
} from "../js/ascent.js";

test("altitude lifts the rocket, and a tier rung can outrun a low total", () => {
  assert.ok(scoreProgress(0) < scoreProgress(5));
  assert.ok(scoreProgress(5) < scoreProgress(35));
  assert.ok(scoreProgress(35) < scoreProgress(70));
  assert.ok(scoreProgress(70) < scoreProgress(700));
  assert.ok(scoreProgress(700) <= 1);
  assert.ok(tierRung("taxi") < tierRung("climb"));
  assert.ok(tierRung("climb") < tierRung("burn"));
  assert.ok(tierRung("burn") < tierRung("stall"));
  assert.ok(tierRung("stall") < tierRung("apogee"));
  assert.ok(tierRung("apogee") < tierRung("escape"));
  assert.ok(rocketProgress(5, "taxi") >= tierRung("taxi"));
  assert.ok(rocketProgress(5, "taxi") > scoreProgress(5));
  assert.ok(rocketProgress(35, "taxi") > rocketProgress(5, "taxi"));
  assert.equal(rocketProgress(100, "escape"), tierRung("escape"));
  assert.ok(rocketProgress(700, "taxi") > tierRung("taxi"));
});

test("peak tier is the best rung reached, ignoring misses", () => {
  assert.equal(peakTier([]), null);
  assert.equal(peakTier([{ tier: null }, { tier: "taxi" }, { tier: "burn" }, { tier: "climb" }]), "burn");
  assert.equal(peakTier([{ tier: "escape" }, { tier: "apogee" }]), "escape");
});

test("bursts grow with the tier and misses fall instead of blooming", () => {
  assert.ok(burstCount("taxi") < burstCount("climb"));
  assert.ok(burstCount("climb") < burstCount("burn"));
  assert.ok(burstCount("burn") < burstCount("stall"));
  assert.ok(burstCount("stall") < burstCount("apogee"));
  assert.ok(burstCount("apogee") < burstCount("escape"));
  assert.equal(burstShape("stall"), "flat");
  assert.equal(burstShape("escape"), "radial");
  assert.equal(burstShape("miss"), "fall");
  assert.equal(burstShape("reject"), "cough");
});

test("the finale and its line scale with how high the flight got", () => {
  assert.equal(finalePops(0, null), 1);
  assert.ok(finalePops(5, "taxi") < finalePops(100, "escape"));
  assert.ok(finalePops(700, "escape") > finalePops(100, "escape"));
  assert.equal(flightMood(5, "taxi"), "low");
  assert.equal(flightMood(10, "climb"), "mid");
  assert.equal(flightMood(60, "apogee"), "high");
  assert.equal(flightMood(100, "escape"), "escape");
  assert.equal(flightMood(700, "taxi"), "escape");
  assert.equal(flightLine("escape"), "Escape velocity.");
  assert.equal(flightLine("low"), "Clear of the pad.");
  assert.equal(flightLine("nope"), "Clear of the pad.");
});
