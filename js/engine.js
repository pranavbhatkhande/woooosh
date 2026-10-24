import { pointsFor, sampleByTier } from "./tiers.js";

export const PREVIEW_MS = 2000;
export const PLAY_MS = 25000;

export function startRun({ mode, date, prompts, now }) {
  if (!prompts || prompts.length < 1) throw new Error("no prompts");
  return {
    mode,
    date,
    prompts,
    index: 0,
    phase: "preview",
    phaseEndsAt: now + PREVIEW_MS,
    altitude: 0,
    rounds: [],
  };
}

function finish(state, round, now) {
  const rounds = state.rounds.concat(round);
  return {
    ...state,
    paused: false,
    remainingMs: 0,
    phase: "reveal",
    phaseEndsAt: now,
    altitude: state.altitude + (round.points || 0),
    rounds,
  };
}

function current(state) {
  return state.prompts[state.index];
}

export function pauseClock(state, now) {
  // One in-flight judge request. A second call does not stack extra time.
  if (!state || state.phase !== "play" || state.paused) return state;
  if (now >= state.phaseEndsAt) return state;
  return { ...state, paused: true, remainingMs: state.phaseEndsAt - now };
}

export function resumeClock(state, now) {
  if (!state || !state.paused) return state;
  const remaining = Math.max(0, state.remainingMs || 0);
  return { ...state, paused: false, remainingMs: 0, phaseEndsAt: now + remaining };
}

export function tick(state, now) {
  if (!state || state.phase === "done" || state.phase === "reveal") return state;
  if (state.paused) return state;
  if (now < state.phaseEndsAt) return state;
  if (state.phase === "preview") {
    return { ...state, phase: "play", phaseEndsAt: now + PLAY_MS };
  }
  const prompt = current(state);
  return finish(state, {
    promptId: prompt.id,
    text: prompt.text,
    kind: "miss",
    typed: "",
    canonical: "",
    tier: null,
    points: 0,
    judged: false,
    examples: sampleByTier(prompt.answers, ""),
  }, now);
}

export function lockAnswer(state, now, hit) {
  if (!state || state.phase !== "play") return state;
  if (!state.paused && now >= state.phaseEndsAt) return state;
  const prompt = current(state);
  const points = hit.points ?? pointsFor(hit.tier);
  return finish(state, {
    promptId: prompt.id,
    text: prompt.text,
    kind: "hit",
    typed: hit.typed || hit.name,
    canonical: hit.name,
    tier: hit.tier,
    points,
    judged: Boolean(hit.judged),
    examples: sampleByTier(prompt.answers, hit.name),
  }, now);
}

export function passPrompt(state, now) {
  if (!state || state.phase !== "play") return state;
  const prompt = current(state);
  return finish(state, {
    promptId: prompt.id,
    text: prompt.text,
    kind: "pass",
    typed: "",
    canonical: "",
    tier: null,
    points: 0,
    judged: false,
    examples: sampleByTier(prompt.answers, ""),
  }, now);
}

export function nextPrompt(state, now) {
  if (!state || state.phase !== "reveal") return state;
  if (state.index + 1 >= state.prompts.length) {
    return { ...state, phase: "done", phaseEndsAt: now };
  }
  return {
    ...state,
    index: state.index + 1,
    phase: "preview",
    phaseEndsAt: now + PREVIEW_MS,
  };
}

export function secondsLeft(state, now) {
  if (!state || state.phase !== "play") return 0;
  if (state.paused) return Math.max(0, Math.ceil((state.remainingMs || 0) / 1000));
  return Math.max(0, Math.ceil((state.phaseEndsAt - now) / 1000));
}
