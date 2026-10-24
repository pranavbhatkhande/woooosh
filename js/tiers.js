import { KM_PER_POINT, MAX_KM } from "./constants.js";

/**
 * Six altitudes, common to rare.
 * Hotshot is the trap: the clever-sounding answer everybody reaches for
 * that is not actually rare.
 * Keep the ids and points aligned with pipeline/tiering.py.
 */
export const TIERS = [
  { id: "pad", points: 5, label: "Pad", trap: false, emoji: "⬜", hue: "var(--pad)" },
  { id: "ascent", points: 10, label: "Ascent", trap: false, emoji: "🟩", hue: "var(--ascent)" },
  { id: "ceiling", points: 25, label: "Ceiling", trap: false, emoji: "🔷", hue: "var(--ceiling)" },
  { id: "hotshot", points: 40, label: "Hotshot", trap: true, emoji: "⭐", hue: "var(--hotshot)" },
  { id: "orbit", points: 60, label: "Orbit", trap: false, emoji: "🟣", hue: "var(--orbit)" },
  { id: "apex", points: 100, label: "Apex", trap: false, emoji: "🔴", hue: "var(--apex)" },
];

export const TIER_BY_ID = Object.fromEntries(TIERS.map((tier) => [tier.id, tier]));

export const MISS_EMOJI = "⬛";
export const GEM_EMOJI = "💎";

export const ZONES = [
  { min: 0, label: "The Pad" },
  { min: 1, label: "Troposphere" },
  { min: 12, label: "Stratosphere" },
  { min: 50, label: "Mesosphere" },
  { min: 80, label: "Kármán Edge" },
  { min: 100, label: "Thermosphere" },
  { min: 200, label: "Low Orbit" },
  { min: 350, label: "High Orbit" },
  { min: 550, label: "Deep Black" },
];

export function pointsFor(tierId) {
  return TIER_BY_ID[tierId]?.points ?? 0;
}

export function tierMeta(tierId) {
  return TIER_BY_ID[tierId] ?? null;
}

export function kmForPoints(points) {
  return points * KM_PER_POINT;
}

export function zoneFor(km) {
  let zone = ZONES[0];
  for (const candidate of ZONES) {
    if (km >= candidate.min) zone = candidate;
  }
  return zone;
}

export function zoneProgress(km) {
  return Math.max(0, Math.min(1, km / MAX_KM));
}

export function blurb(tierId, gem) {
  if (gem) return "Gem. The rare one.";
  switch (tierId) {
    case "pad":
      return "Pad. Almost everyone launches this one.";
    case "ascent":
      return "Ascent. Familiar, and a little less automatic.";
    case "ceiling":
      return "Ceiling. Solid. Not the obvious call.";
    case "hotshot":
      return "Hotshot. The clever pick everyone reaches for. It is not actually rare.";
    case "orbit":
      return "Orbit. That one does not come up often.";
    case "apex":
      return "Apex. Rare air.";
    default:
      return "";
  }
}

export function resultEmoji(entry) {
  if (!entry || entry.outcome !== "hit" || !entry.answer) return MISS_EMOJI;
  if (entry.answer.gem) return GEM_EMOJI;
  return tierMeta(entry.answer.tier)?.emoji ?? MISS_EMOJI;
}
