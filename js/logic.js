/** Plan ranges used by the calculator. These are the figures in the coaching plan, not a new formula. */
export const PROTEIN_G_PER_KG = { low: 1.6, high: 2.2, perMeal: 0.4 };
export const DEFICIT_KCAL = { low: 300, high: 500 };
export const LOSS_FRACTION_PER_WEEK = { low: 0.005, high: 0.007 };
export const FAST_LOSS_FRACTION_PER_WEEK = 0.01;
export const SAMPLE_DAY_KG = 80;
export const KG_PER_LB = 0.45359237;
export const CM_PER_IN = 2.54;

/**
 * Weight change under this percent per week is treated as flat on the check-in screen.
 * The plan says "flat" without a cutoff; this only keeps scale noise from firing stall advice.
 */
export const FLAT_PCT_PER_WEEK = 0.1;
/** Waist change within this many centimeters over the window counts as flat. */
export const FLAT_WAIST_CM = 0.1;

const PHASE_INDEX = [
  { weeks: [0], index: 0 },
  { weeks: [1, 2], index: 1 },
  { weeks: [3, 4, 5], index: 2 },
  { weeks: [6], index: 3 },
  { weeks: [7, 8, 9, 10], index: 4 },
  { weeks: [11], index: 5 },
  { weeks: [12], index: 6 },
];

export function phaseIndexForWeek(week) {
  const w = Number(week);
  const hit = PHASE_INDEX.find((row) => row.weeks.includes(w));
  return hit ? hit.index : null;
}

export function toKg(value, unit) {
  const n = typeof value === "number" ? value : Number(String(value).trim());
  if (!Number.isFinite(n) || n <= 0) return null;
  return unit === "lb" ? n * KG_PER_LB : n;
}

export function fromKg(kg, unit) {
  return unit === "lb" ? kg / KG_PER_LB : kg;
}

function maintenanceKcal(value) {
  if (value == null || String(value).trim() === "") return { ok: true, value: null };
  const n = Number(value);
  if (!Number.isFinite(n) || n < 800 || n > 8000) {
    return {
      ok: false,
      code: "maintenance",
      message: "Enter maintenance as a daily intake between 800 and 8000 kcal, or leave it blank.",
    };
  }
  return { ok: true, value: n };
}

/**
 * Targets from body weight, sex, and activity, using only the plan's published ranges.
 * Sex does not change protein or the loss rate. Activity does not change the deficit.
 * There is no calorie equation in the plan; intake is maintenance minus 300–500 kcal.
 */
export function computeTargets(input) {
  const unit = input.unit === "lb" ? "lb" : "kg";
  const weightKg = toKg(input.weight, unit);
  if (weightKg == null || weightKg < 30 || weightKg > 300) {
    return {
      ok: false,
      code: "weight",
      message: "Enter a body weight between 30 and 300 kg (about 66–660 lb).",
    };
  }

  const maint = maintenanceKcal(input.maintenance);
  if (!maint.ok) return maint;

  let basisKg = weightKg;
  let goalKg = null;
  const bodyComp = input.bodyComp || "unsure";
  if (bodyComp === "higher-fat") {
    goalKg = toKg(input.goalWeight, unit);
    if (goalKg == null) {
      return {
        ok: false,
        code: "goal",
        message: "Enter a goal weight. The plan bases protein on goal weight when there is a lot of fat to lose.",
      };
    }
    if (goalKg < 30 || goalKg > 300) {
      return {
        ok: false,
        code: "goal",
        message: "Enter a goal weight between 30 and 300 kg (about 66–660 lb).",
      };
    }
    if (goalKg >= weightKg) {
      return {
        ok: false,
        code: "goal",
        message: "Goal weight should be below your current weight when protein is based on goal weight.",
      };
    }
    basisKg = goalKg;
  }

  const sex = input.sex === "female" || input.sex === "male" ? input.sex : "unspecified";
  const activity = input.activity === "busy" ? "busy" : "standard";

  return {
    ok: true,
    unit,
    sex,
    activity,
    bodyComp,
    weightKg,
    basisKg,
    goalKg,
    protein: {
      low: PROTEIN_G_PER_KG.low * basisKg,
      high: PROTEIN_G_PER_KG.high * basisKg,
      perMeal: PROTEIN_G_PER_KG.perMeal * basisKg,
    },
    weeklyLossKg: {
      low: weightKg * LOSS_FRACTION_PER_WEEK.low,
      high: weightKg * LOSS_FRACTION_PER_WEEK.high,
    },
    deficitKcal: { ...DEFICIT_KCAL },
    deficitEmphasis: bodyComp === "higher-fat" ? "high" : bodyComp === "lean" ? "low" : "range",
    intake: maint.value == null
      ? null
      : { low: maint.value - DEFICIT_KCAL.high, high: maint.value - DEFICIT_KCAL.low, maintenance: maint.value },
    portionEnd: sex === "male" ? "upper" : sex === "female" ? "lower" : "unspecified",
    sampleScale: weightKg / SAMPLE_DAY_KG,
  };
}

function finiteOrNull(value) {
  if (value == null || value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

export function sortedCheckins(entries) {
  return (entries || [])
    .filter((row) => row && /^\d{4}-\d{2}-\d{2}$/.test(row.date) && finiteOrNull(row.weight) > 0)
    .map((row) => ({
      date: row.date,
      weight: finiteOrNull(row.weight),
      waist: finiteOrNull(row.waist),
      steps: finiteOrNull(row.steps),
      sleep: finiteOrNull(row.sleep),
    }))
    .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
}

/**
 * Rate of change across the last `window` check-ins that have a weight.
 * Percent is of the window's starting weight, per week.
 */
export function trendWindow(entries, window = 3) {
  const points = sortedCheckins(entries);
  if (points.length < 2) {
    return { kind: "need-data", points, count: points.length };
  }
  const recent = points.slice(-window);
  const start = recent[0];
  const end = recent[recent.length - 1];
  const days = (Date.parse(`${end.date}T00:00:00Z`) - Date.parse(`${start.date}T00:00:00Z`)) / 86400000;
  const weeks = days / 7;
  if (!(weeks > 0)) {
    return { kind: "need-span", points: recent, count: points.length };
  }
  const deltaKg = end.weight - start.weight;
  const pctPerWeek = (deltaKg / start.weight) * 100 / weeks;
  const lossPerWeek = -pctPerWeek;
  const waistKnown = start.waist > 0 && end.waist > 0;
  const waistDeltaCm = waistKnown ? end.waist - start.waist : null;
  const weightFlat = Math.abs(pctPerWeek) < FLAT_PCT_PER_WEEK;

  let kind;
  if (lossPerWeek > FAST_LOSS_FRACTION_PER_WEEK * 100) kind = "too-fast";
  else if (lossPerWeek >= 0.5 && lossPerWeek <= 0.7) kind = "on-target";
  else if (weightFlat && waistDeltaCm != null && waistDeltaCm < -FLAT_WAIST_CM) kind = "recomp";
  else if (weightFlat && waistDeltaCm != null && waistDeltaCm > FLAT_WAIST_CM) kind = "flat-waist-up";
  else if (weightFlat) kind = "flat";
  else if (lossPerWeek > 0.7 && lossPerWeek <= 1) kind = "a-bit-fast";
  else if (lossPerWeek > 0 && lossPerWeek < 0.5) kind = "a-bit-slow";
  else if (pctPerWeek > 0) kind = "gaining";
  else kind = "mixed";

  const steps = recent.map((row) => row.steps).filter((n) => n != null && n >= 0);
  const sleep = recent.map((row) => row.sleep).filter((n) => n != null && n >= 0);

  return {
    kind,
    points: recent,
    allPoints: points,
    count: points.length,
    weeks,
    from: start.date,
    to: end.date,
    startKg: start.weight,
    endKg: end.weight,
    deltaKg,
    pctPerWeek,
    lossPerWeek,
    waistDeltaCm,
    weightFlat,
    stepsAvg: steps.length ? steps.reduce((sum, n) => sum + n, 0) / steps.length : null,
    sleepAvg: sleep.length ? sleep.reduce((sum, n) => sum + n, 0) / sleep.length : null,
  };
}
