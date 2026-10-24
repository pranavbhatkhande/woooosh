// Six ascent tiers. STALL is the too-clever band: the obvious "deep cut"
// that is not actually rare. ESCAPE is the single gem on a prompt.

export const TIERS = [
  { id: "taxi", label: "TAXI", points: 5, blurb: "Everyone rolls from here." },
  { id: "climb", label: "CLIMB", points: 10, blurb: "Off the pad." },
  { id: "burn", label: "BURN", points: 25, blurb: "Main engine burn." },
  { id: "stall", label: "STALL", points: 40, blurb: "Too clever. That pick stalls.", trap: true },
  { id: "apogee", label: "APOGEE", points: 60, blurb: "High, and actually rare." },
  { id: "escape", label: "ESCAPE", points: 100, blurb: "Escape velocity. The gem.", gem: true },
];

export const TIER_IDS = TIERS.map((tier) => tier.id);

const BY_ID = new Map(TIERS.map((tier) => [tier.id, tier]));

export function tierMeta(id) {
  return BY_ID.get(id) || null;
}

export function pointsFor(id) {
  return BY_ID.get(id)?.points ?? 0;
}

// Familiarity 10 = almost everyone knows it. Judged answers never reach ESCAPE.
export function tierForFamiliarity(value) {
  const n = Math.round(Number(value));
  if (!Number.isFinite(n)) return null;
  const f = Math.max(1, Math.min(10, n));
  if (f >= 9) return "taxi";
  if (f >= 7) return "climb";
  if (f >= 5) return "burn";
  if (f >= 3) return "stall";
  return "apogee";
}

export const ZONES = [
  { id: "pad", label: "THE PAD", min: 0 },
  { id: "tropo", label: "TROPOSPHERE", min: 1 },
  { id: "strato", label: "STRATOSPHERE", min: 12 },
  { id: "meso", label: "MESOSPHERE", min: 50 },
  { id: "thermo", label: "THERMOSPHERE", min: 85 },
  { id: "low", label: "LOW ORBIT", min: 150 },
  { id: "high", label: "HIGH ORBIT", min: 400 },
  { id: "deep", label: "DEEP SPACE", min: 600 },
];

export function zoneFor(km) {
  let zone = ZONES[0];
  for (const candidate of ZONES) {
    if (km >= candidate.min) zone = candidate;
  }
  return zone;
}

export const CEILING_KM = 700;

export function sampleByTier(answers, chosenName) {
  const chosen = (chosenName || "").toLowerCase();
  const out = [];
  for (const tier of TIERS) {
    const hit = (answers || []).find(
      (answer) => answer.tier === tier.id && answer.name.toLowerCase() !== chosen,
    );
    if (hit) out.push(hit);
  }
  return out;
}
