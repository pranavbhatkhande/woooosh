// How a typed answer becomes a lock or a shake.
// Exact bank hits never wait on the model. A judge failure uses the bank's
// fuzzy match. A judge reject does not.

import { exactHit, matchAnswer } from "./match.js";

const TIER_OK = new Set(["taxi", "climb", "burn", "stall", "apogee", "escape"]);

function bankHit(answer) {
  return { name: answer.name, tier: answer.tier, judged: false };
}

function acceptedTier(data) {
  if (!data || !TIER_OK.has(data.tier)) return "";
  if (data.inBank) return data.tier;
  if (data.tier === "escape") return "apogee";
  return data.tier;
}

export function scoreAttempt(compiled, typed, attempt) {
  const exact = exactHit(compiled, typed);
  if (exact) return { action: "lock", hit: bankHit(exact) };
  const status = attempt && attempt.status;
  if (status === "scored") {
    const data = attempt.data || {};
    const tier = acceptedTier(data);
    if (!tier) return { action: "shake", remember: true };
    const hit = {
      name: data.canonical || String(typed || ""),
      tier,
      judged: !data.inBank,
    };
    if (Number.isFinite(data.points)) hit.points = data.points;
    return { action: "lock", hit };
  }
  if (status === "reject") return { action: "shake", remember: true };
  if (status === "off" || status === "fallback") {
    const fuzzy = matchAnswer(compiled, typed);
    if (fuzzy) return { action: "lock", hit: bankHit(fuzzy) };
    return { action: "shake", remember: false };
  }
  return { action: "continue" };
}
