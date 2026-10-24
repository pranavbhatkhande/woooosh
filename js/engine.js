import { PLAY_MS, PREVIEW_MS } from "./constants.js";
import { matchAnswer, prepareAnswers } from "./matcher.js";
import { blurb, kmForPoints, pointsFor, resultEmoji, zoneFor } from "./tiers.js";

export function startRun({ prompts, mode, date = null, now }) {
  return {
    mode,
    date,
    prompts,
    index: 0,
    phase: prompts.length ? "preview" : "done",
    phaseEndsAt: prompts.length ? now + PREVIEW_MS : null,
    entries: prompts.map((prompt) => ({
      promptId: prompt.id,
      text: prompt.text,
      outcome: "pending",
      answer: null,
      raw: "",
    })),
    lastReject: null,
  };
}

function lock(run, entry) {
  const entries = run.entries.map((row, index) => (
    index === run.index ? { ...row, ...entry } : row
  ));
  return {
    ...run,
    entries,
    phase: "result",
    phaseEndsAt: null,
    lastReject: null,
  };
}

export function advance(run, now) {
  if (!run || run.phase === "done" || run.phase === "result" || run.phaseEndsAt == null) return run;
  if (now < run.phaseEndsAt) return run;
  if (run.phase === "preview") {
    return { ...run, phase: "play", phaseEndsAt: now + PLAY_MS, lastReject: null };
  }
  if (run.phase === "play") {
    return lock(run, { outcome: "timeout", answer: null, raw: "" });
  }
  return run;
}

export function reconcile(run, now) {
  if (!run) return run;
  if (run.phase === "preview" && run.phaseEndsAt != null && now >= run.phaseEndsAt) {
    return { ...run, phase: "play", phaseEndsAt: now + PLAY_MS, lastReject: null };
  }
  return advance(run, now);
}

export function submitAnswer(run, raw, now) {
  if (!run || run.phase !== "play") {
    return { run, accepted: false, reason: "closed" };
  }
  const text = String(raw ?? "");
  if (!text.trim()) {
    return { run, accepted: false, reason: "empty" };
  }
  const prompt = run.prompts[run.index];
  const prepared = prompt.prepared || prepareAnswers(prompt.answers);
  const hit = matchAnswer(text, prompt.answers, prepared);
  if (!hit) {
    return {
      run: { ...run, lastReject: text },
      accepted: false,
      reason: "miss",
    };
  }
  const answer = {
    name: hit.name,
    tier: hit.tier,
    gem: hit.gem,
    points: pointsFor(hit.tier),
    via: hit.via,
  };
  return {
    run: lock(run, { outcome: "hit", answer, raw: text.trim() }),
    accepted: true,
    reason: "hit",
  };
}

export function passPrompt(run, now) {
  if (!run || run.phase !== "play") {
    return { run, accepted: false, reason: "closed" };
  }
  return {
    run: lock(run, { outcome: "pass", answer: null, raw: "" }),
    accepted: true,
    reason: "pass",
  };
}

export function nextPrompt(run, now) {
  if (!run || run.phase !== "result") return run;
  const index = run.index + 1;
  if (index >= run.prompts.length) {
    return { ...run, index, phase: "done", phaseEndsAt: null, lastReject: null };
  }
  return {
    ...run,
    index,
    phase: "preview",
    phaseEndsAt: now + PREVIEW_MS,
    lastReject: null,
  };
}

export function totalPoints(run) {
  return (run?.entries || []).reduce((sum, entry) => sum + (entry.answer?.points || 0), 0);
}

export function totalKm(run) {
  return kmForPoints(totalPoints(run));
}

export function sampleOthers(prompt, hitName) {
  const picked = [];
  const seen = new Set();
  for (const answer of prompt.answers || []) {
    if (answer.name === hitName || seen.has(answer.tier)) continue;
    seen.add(answer.tier);
    picked.push(answer);
  }
  const gem = (prompt.answers || []).find((answer) => answer.gem && answer.name !== hitName);
  if (gem && !picked.some((answer) => answer.name === gem.name)) picked.unshift(gem);
  return picked.slice(0, 5);
}

export function shareText(run, origin = "https://woooosh.ai") {
  const icons = (run.entries || []).map((entry) => resultEmoji(entry)).join("");
  const km = totalKm(run);
  const zone = zoneFor(km).label;
  const head = run.mode === "daily" && run.date
    ? `WOOOOSH · Daily · ${run.date}`
    : "WOOOOSH · Unlimited";
  return `${head}\n${icons}\n${km} km · ${zone}\n${origin}`;
}

export function entryBlurb(entry) {
  if (!entry || entry.outcome === "pending") return "";
  if (entry.outcome === "timeout") return "The window closed. 0 km on this one.";
  if (entry.outcome === "pass") return "Passed. 0 km. The next prompt is already on the rail.";
  return blurb(entry.answer?.tier, entry.answer?.gem);
}

export function secondsLeft(run, now) {
  if (!run?.phaseEndsAt || (run.phase !== "play" && run.phase !== "preview")) return 0;
  return Math.max(0, (run.phaseEndsAt - now) / 1000);
}
