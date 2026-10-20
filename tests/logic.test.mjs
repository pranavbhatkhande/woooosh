import assert from "node:assert/strict";
import {
  CM_PER_IN,
  FAST_LOSS_FRACTION_PER_WEEK,
  KG_PER_LB,
  PROTEIN_G_PER_KG,
  computeTargets,
  phaseIndexForWeek,
  trendWindow,
} from "../js/logic.js";
import { levers, phases, references, sessions, templates } from "../js/data.js";

assert.equal(PROTEIN_G_PER_KG.low, 1.6);
assert.equal(PROTEIN_G_PER_KG.high, 2.2);
assert.equal(PROTEIN_G_PER_KG.perMeal, 0.4);
assert.equal(FAST_LOSS_FRACTION_PER_WEEK, 0.01);

assert.equal(levers.length, 10);
assert.equal(levers[0].target.includes("300–500"), true);
assert.equal(levers[2].target.includes("1.6–2.2"), true);
assert.equal(templates.length, 3);
assert.equal(phases.length, 7);
assert.equal(sessions.A.length, 7);
assert.equal(sessions.B.length, 7);
assert.equal(sessions.C.length, 8);
assert.equal(references.length, 61);
assert.equal(references[0].n, 1);
assert.match(references[0].citation, /Pontzer/);
assert.equal(references[60].n, 61);
assert.match(references[60].citation, /Knowler/);
assert.match(references[33].citation, /Nedeltcheva/);

for (let week = 0; week <= 12; week += 1) {
  assert.equal(typeof phaseIndexForWeek(week), "number");
}
assert.equal(phaseIndexForWeek(0), 0);
assert.equal(phaseIndexForWeek(2), 1);
assert.equal(phaseIndexForWeek(5), 2);
assert.equal(phaseIndexForWeek(6), 3);
assert.equal(phaseIndexForWeek(10), 4);
assert.equal(phaseIndexForWeek(11), 5);
assert.equal(phaseIndexForWeek(12), 6);
assert.equal(phaseIndexForWeek(13), null);

const base = computeTargets({
  weight: 80,
  unit: "kg",
  sex: "unspecified",
  bodyComp: "unsure",
  activity: "standard",
  maintenance: "",
});
assert.equal(base.ok, true);
assert.equal(base.protein.low, 128);
assert.equal(base.protein.high, 176);
assert.equal(base.protein.perMeal, 32);
assert.equal(base.weeklyLossKg.low, 0.4);
assert.equal(base.weeklyLossKg.high, 0.56);
assert.equal(base.intake, null);
assert.equal(base.deficitEmphasis, "range");
assert.equal(base.sampleScale, 1);

const withIntake = computeTargets({
  weight: 80,
  unit: "kg",
  sex: "male",
  bodyComp: "unsure",
  activity: "standard",
  maintenance: 2500,
});
assert.equal(withIntake.intake.low, 2000);
assert.equal(withIntake.intake.high, 2200);
assert.equal(withIntake.portionEnd, "upper");

const female = computeTargets({
  weight: 80,
  unit: "kg",
  sex: "female",
  bodyComp: "lean",
  activity: "busy",
  maintenance: "",
});
assert.equal(female.protein.low, 128);
assert.equal(female.deficitEmphasis, "low");
assert.equal(female.portionEnd, "lower");
assert.equal(female.activity, "busy");

const higherFat = computeTargets({
  weight: 100,
  unit: "kg",
  sex: "male",
  bodyComp: "higher-fat",
  goalWeight: 80,
  activity: "standard",
  maintenance: 3000,
});
assert.equal(higherFat.basisKg, 80);
assert.equal(higherFat.protein.low, 128);
assert.equal(higherFat.protein.high, 176);
assert.equal(higherFat.weeklyLossKg.low, 0.5);
assert.equal(higherFat.deficitEmphasis, "high");
assert.equal(higherFat.intake.low, 2500);
assert.equal(higherFat.intake.high, 2700);

assert.equal(computeTargets({ weight: "", unit: "kg" }).ok, false);
assert.equal(
  computeTargets({ weight: 100, unit: "kg", bodyComp: "higher-fat", goalWeight: "" }).code,
  "goal",
);
assert.equal(
  computeTargets({ weight: 80, unit: "kg", bodyComp: "higher-fat", goalWeight: 90 }).code,
  "goal",
);
assert.equal(computeTargets({ weight: 80, unit: "kg", maintenance: 100 }).code, "maintenance");

const lb = computeTargets({ weight: 176, unit: "lb", sex: "unspecified", bodyComp: "unsure" });
assert.equal(lb.ok, true);
assert.ok(Math.abs(lb.weightKg - 176 * KG_PER_LB) < 1e-9);
assert.ok(Math.abs(lb.protein.low - 1.6 * 176 * KG_PER_LB) < 1e-9);

const dates = (rows) => rows.map((row) => ({ waist: null, steps: null, sleep: null, ...row }));

assert.equal(trendWindow(dates([{ date: "2026-01-01", weight: 80 }])).kind, "need-data");
assert.equal(
  trendWindow(dates([
    { date: "2026-01-01", weight: 80 },
    { date: "2026-01-01", weight: 79 },
  ])).kind,
  "need-span",
);

const onTarget = trendWindow(dates([
  { date: "2026-01-01", weight: 80, waist: 90 },
  { date: "2026-01-08", weight: 79.6, waist: 90 },
]));
assert.equal(onTarget.kind, "on-target");
assert.ok(Math.abs(onTarget.lossPerWeek - 0.5) < 1e-9);

const tooFast = trendWindow(dates([
  { date: "2026-01-01", weight: 80 },
  { date: "2026-01-08", weight: 79.1 },
]));
assert.equal(tooFast.kind, "too-fast");

const recomp = trendWindow(dates([
  { date: "2026-01-01", weight: 80, waist: 90 },
  { date: "2026-01-15", weight: 80, waist: 89 },
]));
assert.equal(recomp.kind, "recomp");

const flat = trendWindow(dates([
  { date: "2026-01-01", weight: 80, waist: 90, steps: 6000, sleep: 6.5 },
  { date: "2026-01-08", weight: 80.02, waist: 90, steps: 7000, sleep: 7.5 },
]));
assert.equal(flat.kind, "flat");
assert.equal(flat.stepsAvg, 6500);
assert.equal(flat.sleepAvg, 7);

const flatNoWaist = trendWindow(dates([
  { date: "2026-01-01", weight: 80 },
  { date: "2026-01-08", weight: 80 },
]));
assert.equal(flatNoWaist.kind, "flat");
assert.equal(flatNoWaist.waistDeltaCm, null);

const slow = trendWindow(dates([
  { date: "2026-01-01", weight: 80 },
  { date: "2026-01-08", weight: 79.84 },
]));
assert.equal(slow.kind, "a-bit-slow");

const gaining = trendWindow(dates([
  { date: "2026-01-01", weight: 80 },
  { date: "2026-01-08", weight: 80.4 },
]));
assert.equal(gaining.kind, "gaining");

const windowed = trendWindow(dates([
  { date: "2026-01-01", weight: 82 },
  { date: "2026-01-08", weight: 81 },
  { date: "2026-01-15", weight: 80.2 },
  { date: "2026-01-22", weight: 79.7 },
]), 3);
assert.equal(windowed.points.length, 3);
assert.equal(windowed.from, "2026-01-08");
assert.equal(windowed.kind, "a-bit-fast");

assert.equal(CM_PER_IN, 2.54);

console.log("logic tests passed");
