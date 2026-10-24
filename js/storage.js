import { shiftDate } from "./daily.js";

export const STORAGE_KEY = "woooosh.launch.v1";
export const SESSION_KEY = "woooosh.launch.run";

export function emptyStats() {
  return {
    streak: 0,
    bestStreak: 0,
    lastDaily: null,
    bestKm: 0,
    runs: 0,
    unlimited: null,
    lastDailyResult: null,
    lastUnlimitedResult: null,
  };
}

export function loadStats(storage) {
  const target = storage || globalThis.localStorage;
  try {
    const raw = target?.getItem(STORAGE_KEY);
    if (!raw) return emptyStats();
    const parsed = JSON.parse(raw);
    return { ...emptyStats(), ...parsed };
  } catch {
    return emptyStats();
  }
}

export function saveStats(stats, storage) {
  const target = storage || globalThis.localStorage;
  try {
    target?.setItem(STORAGE_KEY, JSON.stringify(stats));
  } catch {
    /* private mode and blocked storage still play the current run */
  }
  return stats;
}

export function recordResult(stats, summary) {
  const base = { ...emptyStats(), ...stats };
  const bestKm = Math.max(base.bestKm || 0, summary.km || 0);
  const runs = (base.runs || 0) + 1;
  if (summary.mode !== "daily") {
    return {
      ...base,
      bestKm,
      runs,
      lastUnlimitedResult: summary,
    };
  }
  if (base.lastDaily === summary.date) {
    return { ...base, bestKm, lastDailyResult: summary };
  }
  const continued = base.lastDaily && shiftDate(summary.date, -1) === base.lastDaily;
  const streak = continued ? (base.streak || 0) + 1 : 1;
  return {
    ...base,
    streak,
    bestStreak: Math.max(base.bestStreak || 0, streak),
    lastDaily: summary.date,
    bestKm,
    runs,
    lastDailyResult: summary,
  };
}
