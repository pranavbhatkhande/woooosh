import { TIER_IDS } from "./tiers.js";

export const MARK = {
  miss: "⬛",
  pass: "⬛",
  taxi: "⬜",
  climb: "🟩",
  burn: "🟨",
  stall: "🟧",
  apogee: "🟪",
  escape: "💠",
};

export function roundMark(round) {
  if (!round || round.points <= 0 || !TIER_IDS.includes(round.tier)) return MARK.miss;
  return MARK[round.tier] || MARK.miss;
}

export function shareText({ mode, date, altitude, zone, rounds }) {
  const grid = (rounds || []).map(roundMark).join("");
  const head = mode === "daily" ? `WOOOOSH · DAILY · ${date}` : "WOOOOSH · UNLIMITED";
  const height = `${altitude} km · ${zone}`;
  return `${head}\n${height}\n${grid}\n\nwoooosh.ai`;
}
