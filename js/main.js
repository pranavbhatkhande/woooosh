import { RUN_LENGTH } from "./constants.js";
import { loadBank } from "./bank.js";
import { idsForDate, todayUTC } from "./daily.js";
import { createDeck, takeRun } from "./deck.js";
import {
  advance,
  nextPrompt,
  passPrompt,
  reconcile,
  startRun,
  submitAnswer,
  totalKm,
} from "./engine.js";
import { SESSION_KEY, loadStats, recordResult, saveStats } from "./storage.js";
import { zoneFor } from "./tiers.js";
import {
  patchTimer,
  renderDone,
  renderError,
  renderHelp,
  renderHome,
  renderLoading,
  renderRun,
  setBankNote,
} from "./ui.js";

const main = document.getElementById("main");
const state = {
  bank: null,
  stats: loadStats(),
  screen: "loading",
  run: null,
  ids: [],
  draft: "",
  copied: false,
};

let clock = 0;
let composing = false;

main.addEventListener("click", onClick);
main.addEventListener("submit", onSubmit);
main.addEventListener("input", (event) => {
  if (event.target?.id === "answer") state.draft = event.target.value;
});
main.addEventListener("compositionstart", () => {
  composing = true;
});
main.addEventListener("compositionend", () => {
  composing = false;
});

boot();

async function boot() {
  renderLoading(main);
  try {
    state.bank = await loadBank();
    setBankNote(state.bank);
    const saved = loadSession();
    if (saved) {
      const prompts = await state.bank.promptsFor(saved.ids);
      state.ids = saved.ids;
      state.run = reconcile({ ...saved.run, prompts }, Date.now());
      state.screen = state.run.phase === "done" ? "done" : "run";
      if (state.screen === "done") finish(false);
    } else {
      state.screen = "home";
    }
  } catch (error) {
    renderError(main, error?.message || "The prompt bank did not load.");
    return;
  }
  render();
}

function render() {
  if (!state.bank) return;
  const now = Date.now();
  if (state.screen === "home") {
    const today = todayUTC();
    renderHome(main, {
      stats: state.stats,
      bank: state.bank,
      resume: Boolean(loadSession()),
      today,
      already: state.stats.lastDaily === today && state.stats.lastDailyResult,
    });
  } else if (state.screen === "help") {
    renderHelp(main);
  } else if (state.screen === "run") {
    renderRun(main, { run: state.run, now, draft: state.draft });
    if (state.run.phase === "play") document.getElementById("answer")?.focus();
    if (state.run.phase === "result") document.getElementById("next")?.focus();
  } else if (state.screen === "done") {
    renderDone(main, { run: state.run, copied: state.copied });
  }
  syncClock();
}

function syncClock() {
  stopClock();
  if (state.screen === "run" && (state.run?.phase === "play" || state.run?.phase === "preview")) {
    clock = window.setInterval(tick, 100);
  }
}

function stopClock() {
  if (clock) window.clearInterval(clock);
  clock = 0;
}

function tick() {
  if (state.screen !== "run" || !state.run) return;
  const now = Date.now();
  const next = advance(state.run, now);
  if (next !== state.run) {
    state.run = next;
    state.draft = "";
    saveSession();
    render();
    return;
  }
  patchTimer(state.run, now);
}

function onClick(event) {
  const button = event.target.closest("button");
  if (!button) return;
  const id = button.id;
  if (id === "daily") startDaily();
  else if (id === "unlimited") startUnlimited();
  else if (id === "help") {
    state.screen = "help";
    render();
  } else if (id === "home") goHome();
  else if (id === "resume") resume();
  else if (id === "pass") onPass();
  else if (id === "next") onNext();
  else if (id === "share") onShare();
  else if (id === "again") onAgain();
}

function onSubmit(event) {
  if (event.target?.id !== "answer-form") return;
  event.preventDefault();
  if (composing) return;
  const input = document.getElementById("answer");
  if (!input || input.disabled) return;
  const result = submitAnswer(state.run, input.value, Date.now());
  state.run = result.run;
  if (result.reason === "miss") {
    state.draft = input.value;
    saveSession();
    const note = document.getElementById("reject");
    if (note) note.textContent = "Not in the bank. Try another.";
    input.classList.remove("shake");
    void input.offsetWidth;
    input.classList.add("shake");
    return;
  }
  if (!result.accepted) return;
  state.draft = "";
  saveSession();
  render();
}

async function startDaily() {
  const date = todayUTC();
  const ids = idsForDate(state.bank.daily, state.bank.ids, date);
  await begin(ids, "daily", date);
}

async function startUnlimited() {
  const deck = state.stats.unlimited || createDeck(state.bank.ids);
  const draw = takeRun(deck, state.bank.ids, RUN_LENGTH);
  const ok = await begin(draw.ids, "unlimited", null);
  if (ok) state.stats = saveStats({ ...state.stats, unlimited: draw.deck });
}

async function begin(ids, mode, date) {
  try {
    const prompts = await state.bank.promptsFor(ids);
    state.ids = ids;
    state.draft = "";
    state.copied = false;
    state.run = startRun({ prompts, mode, date, now: Date.now() });
    state.screen = "run";
    saveSession();
    render();
    return true;
  } catch (error) {
    renderError(main, error?.message || "Those prompts did not load.");
    return false;
  }
}

async function resume() {
  const saved = loadSession();
  if (!saved) {
    state.screen = "home";
    render();
    return;
  }
  const prompts = await state.bank.promptsFor(saved.ids);
  state.ids = saved.ids;
  state.run = reconcile({ ...saved.run, prompts }, Date.now());
  state.screen = state.run.phase === "done" ? "done" : "run";
  render();
}

function onPass() {
  if (state.run?.phase !== "play") return;
  const result = passPrompt(state.run, Date.now());
  if (!result.accepted) return;
  state.run = result.run;
  state.draft = "";
  saveSession();
  render();
}

function onNext() {
  if (state.run?.phase !== "result") return;
  state.run = nextPrompt(state.run, Date.now());
  state.draft = "";
  if (state.run.phase === "done") {
    finish(true);
    return;
  }
  saveSession();
  render();
}

function finish(record) {
  if (record) {
    const km = totalKm(state.run);
    const summary = {
      mode: state.run.mode,
      date: state.run.date,
      km,
      zone: zoneFor(km).label,
      entries: state.run.entries.map((entry) => ({
        outcome: entry.outcome,
        text: entry.text,
        answer: entry.answer
          ? {
            name: entry.answer.name,
            tier: entry.answer.tier,
            gem: entry.answer.gem,
            points: entry.answer.points,
          }
          : null,
      })),
    };
    state.stats = saveStats(recordResult(state.stats, summary));
  }
  clearSession();
  state.screen = "done";
  state.copied = false;
  render();
}

async function onShare() {
  const text = document.getElementById("share-text")?.textContent || "";
  try {
    await navigator.clipboard.writeText(text);
    state.copied = true;
  } catch {
    state.copied = false;
    const area = document.createElement("textarea");
    area.value = text;
    document.body.appendChild(area);
    area.select();
    try {
      document.execCommand("copy");
      state.copied = true;
    } catch {
      state.copied = false;
    }
    area.remove();
  }
  render();
}

function onAgain() {
  if (state.run?.mode === "unlimited") startUnlimited();
  else goHome();
}

function goHome() {
  stopClock();
  if (state.run && state.run.phase !== "done") saveSession();
  state.screen = "home";
  state.copied = false;
  render();
}

function saveSession() {
  if (!state.run || state.run.phase === "done") return;
  const payload = {
    ids: state.ids,
    run: {
      mode: state.run.mode,
      date: state.run.date,
      index: state.run.index,
      phase: state.run.phase,
      phaseEndsAt: state.run.phaseEndsAt,
      entries: state.run.entries,
      lastReject: state.run.lastReject,
    },
  };
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(payload));
  } catch {
    /* the run still finishes in this tab */
  }
}

function loadSession() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed?.ids?.length || !parsed.run) return null;
    return parsed;
  } catch {
    return null;
  }
}

function clearSession() {
  try {
    sessionStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
}
