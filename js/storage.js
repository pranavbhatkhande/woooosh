// Local record of seen prompts, the unlimited deck, and a few stats.
// Nothing here is an account.

const KEY = "woooosh.ascent.v1";

function blank() {
  return {
    seen: {},
    deck: [],
    seed: (Math.floor(Math.random() * 1_000_000_000) >>> 0) || 1,
    judge: null,
    stats: { streak: 0, lastDaily: "", best: 0, runs: 0 },
  };
}

export function loadState() {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return blank();
    const data = JSON.parse(raw);
    const base = blank();
    return {
      ...base,
      ...data,
      seen: data.seen && typeof data.seen === "object" ? data.seen : {},
      deck: Array.isArray(data.deck) ? data.deck : [],
      stats: { ...base.stats, ...(data.stats || {}) },
    };
  } catch {
    return blank();
  }
}

export function saveState(state) {
  localStorage.setItem(KEY, JSON.stringify(state));
}
