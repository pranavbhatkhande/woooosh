import { loadIndex, loadPrompts, allIds } from "./bank.js";
import { lockAnswer, nextPrompt, passPrompt, secondsLeft, startRun, tick } from "./engine.js";
import { askJudge, judgePreferred, probeJudge, warmJudge } from "./judge-client.js";
import { compileAnswers, normalize } from "./match.js";
import { scoreAttempt } from "./scoring.js";
import { planUnlimited, dailyPromptIds, previousUtcDate, utcDate } from "./select.js";
import { shareText } from "./share.js";
import { loadState, saveState } from "./storage.js";
import { CEILING_KM, tierMeta, zoneFor } from "./tiers.js";

const screen = document.querySelector("#screen");
const howDialog = document.querySelector("#how");
const settingsDialog = document.querySelector("#settings");
const judgeToggle = document.querySelector("#judge-toggle");
const judgeNote = document.querySelector("#judge-note");
const openHow = document.querySelector("#open-how");
const openSettings = document.querySelector("#open-settings");

const RING = 2 * Math.PI * 28;

let bank = null;
let store = loadState();
let judgeOn = false;
let run = null;
let mode = "daily";
let compiled = new WeakMap();
let rejected = new Set();
let judgeToken = 0;
let judgeAbort = null;
let judging = false;
let view = "";
let nodes = null;
let lastSecond = -1;

function el(tag, attrs, kids) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else node.setAttribute(key, value);
  }
  for (const kid of kids || []) node.append(kid);
  return node;
}

function answersFor(prompt) {
  let ready = compiled.get(prompt);
  if (!ready) {
    ready = compileAnswers(prompt.answers);
    compiled.set(prompt, ready);
  }
  return ready;
}

function noteSeen(id) {
  if (!store.seen[id]) store.seen[id] = Date.now();
  store.deck = (store.deck || []).filter((item) => item !== id);
  saveState(store);
}

function rememberDeck(ids) {
  const plan = planUnlimited(ids, store);
  store.deck = plan.deck;
  store.seed = store.seed || 1;
  saveState(store);
  return plan.deck.slice(0, 7);
}

function recordFinish() {
  const stats = store.stats;
  stats.runs += 1;
  stats.best = Math.max(stats.best || 0, run.altitude);
  if (run.mode === "daily" && stats.lastDaily !== run.date) {
    stats.streak = stats.lastDaily === previousUtcDate(run.date) ? (stats.streak || 0) + 1 : 1;
    stats.lastDaily = run.date;
  }
  saveState(store);
}

function abortJudge() {
  judgeToken += 1;
  if (judgeAbort) judgeAbort.abort();
  judgeAbort = null;
  judging = false;
}

function useJudge() {
  return judgePreferred(store.judge, judgeOn);
}

function syncSettings() {
  const available = judgeOn;
  judgeToggle.checked = useJudge();
  judgeToggle.disabled = !available;
  judgeNote.textContent = available
    ? "Close spellings and real answers that are not in the bank go to the judge. A bank match keeps its tier. Judged answers are marked and never earn ESCAPE. If the judge is unavailable, the bank is used instead. The clock keeps running."
    : "The judge is offline, so scoring stays on the bank, including close spellings.";
}

openHow.addEventListener("click", () => howDialog.showModal());
openSettings.addEventListener("click", () => {
  syncSettings();
  settingsDialog.showModal();
});
judgeToggle.addEventListener("change", () => {
  if (!judgeOn) {
    judgeToggle.checked = false;
    return;
  }
  store.judge = judgeToggle.checked;
  saveState(store);
  syncSettings();
});

function showBoot(message) {
  screen.replaceChildren(el("p", { class: "status", text: message }));
}

function showHome() {
  view = "home";
  nodes = null;
  abortJudge();
  const stats = store.stats || {};
  const date = utcDate();
  screen.replaceChildren(
    el("section", { class: "home" }, [
      el("p", { class: "eyebrow", text: "THE DAILY ASCENT" }),
      el("h1", { class: "title", text: "WOOOOSH" }),
      el("p", { class: "lede", text: "Seven prompts. Rarer answers climb higher." }),
      el("p", { class: "meta", text: `${date} · ${bank.promptCount} prompts in the bank` }),
      el("div", { class: "actions" }, [
        button("Today's ascent", "daily", () => begin("daily")),
        button("Open sky", "ghost", () => begin("unlimited")),
      ]),
      el("dl", { class: "stats" }, [
        stat("Streak", stats.streak ? `${stats.streak} day${stats.streak === 1 ? "" : "s"}` : "—"),
        stat("Best", stats.runs ? `${stats.best || 0} km` : "—"),
        stat("Runs", String(stats.runs || 0)),
      ]),
    ]),
  );
}

function button(label, kind, onClick) {
  const node = el("button", { type: "button", class: `btn ${kind}` }, [label]);
  node.addEventListener("click", onClick);
  return node;
}

function stat(label, value) {
  return el("div", {}, [el("dt", { text: label }), el("dd", { text: value })]);
}

let starting = false;

async function begin(nextMode) {
  if (starting) return;
  starting = true;
  mode = nextMode;
  showBoot("Fueling the round…");
  const ids = allIds(bank);
  const date = utcDate();
  let chosen = [];
  try {
    if (nextMode === "daily") chosen = dailyPromptIds(ids, date, 7);
    else {
      rememberDeck(ids);
      chosen = store.deck.slice(0, 7);
    }
    const prompts = await loadPrompts(bank, chosen);
    if (prompts.length < 1) throw new Error("empty");
    run = startRun({ mode: nextMode, date, prompts, now: Date.now() });
    rejected = new Set();
    if (useJudge()) warmJudge();
    renderPhase();
  } catch {
    screen.replaceChildren(
      el("p", { class: "status", text: "The bank didn't load." }),
      button("Try again", "daily", () => boot()),
    );
  } finally {
    starting = false;
  }
}

function renderPhase() {
  if (!run) return;
  if (run.phase === "done") {
    if (view !== "done") {
      recordFinish();
      renderDone();
    }
    return;
  }
  if (run.phase === "reveal") {
    renderReveal();
    return;
  }
  renderPlay();
}

function dots() {
  const row = el("ol", { class: "dots" });
  run.prompts.forEach((_, index) => {
    const round = run.rounds[index];
    const item = el("li", {
      class: round ? `dot ${round.tier || "miss"}` : index === run.index ? "dot now" : "dot",
    });
    item.setAttribute("aria-hidden", "true");
    row.append(item);
  });
  return row;
}

function meter() {
  const zone = zoneFor(run.altitude);
  const fill = el("span", { class: "meter-fill" });
  fill.style.height = `${Math.max(4, Math.min(100, (run.altitude / CEILING_KM) * 100))}%`;
  const bar = el("div", { class: "meter", role: "img", "aria-label": `${run.altitude} kilometers, ${zone.label}` }, [
    fill,
  ]);
  return el("div", { class: "altitude" }, [
    bar,
    el("div", {}, [
      el("p", { class: "km", text: `${run.altitude} km` }),
      el("p", { class: "zone", text: zone.label }),
    ]),
  ]);
}

function renderPlay() {
  view = "play";
  rejected = new Set();
  const prompt = run.prompts[run.index];
  noteSeen(prompt.id);
  const form = el("form", { class: "answer" });
  const field = el("input", {
    class: "field",
    type: "text",
    name: "answer",
    maxlength: "60",
    autocomplete: "off",
    autocapitalize: "off",
    spellcheck: "false",
    enterkeyhint: "done",
    "aria-label": "Your answer",
    placeholder: "One answer",
  });
  const submit = el("button", { class: "btn daily", type: "submit", text: "Lock in" });
  form.append(field, submit);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    submitAnswer(field.value);
  });
  const pass = button("Pass", "ghost pass", () => {
    abortJudge();
    run = passPrompt(run, Date.now());
    renderPhase();
  });
  const ring = ringSvg();
  const judgingNote = el("p", { class: "judging", role: "status", text: "Judging" });
  judgingNote.hidden = true;
  const live = el("p", { class: "sr", "aria-live": "polite" });
  nodes = { field, ringValue: ring.querySelector(".value"), seconds: ring.querySelector("text"), live, judgingNote, pass };
  const preview = run.phase === "preview";
  field.disabled = preview;
  submit.disabled = preview;
  pass.disabled = preview;
  screen.replaceChildren(
    el("section", { class: "round" }, [
      meter(),
      dots(),
      el("p", { class: "count", text: `${run.index + 1} / ${run.prompts.length}` }),
      el("h2", { class: "prompt", text: prompt.text }),
      el("div", { class: "clock" }, [ring, el("p", { class: "phase", text: preview ? "Read it" : "Name one" })]),
      form,
      judgingNote,
      pass,
      live,
    ]),
  );
  if (!preview) field.focus();
  else screen.focus();
  lastSecond = -1;
  updateClock(Date.now());
}

function ringSvg() {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 72 72");
  svg.setAttribute("class", "ring");
  svg.setAttribute("aria-hidden", "true");
  for (const name of ["track", "value"]) {
    const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    circle.setAttribute("cx", "36");
    circle.setAttribute("cy", "36");
    circle.setAttribute("r", "28");
    circle.setAttribute("class", name);
    if (name === "value") {
      circle.style.strokeDasharray = String(RING);
      circle.style.strokeDashoffset = "0";
    }
    svg.append(circle);
  }
  const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
  label.setAttribute("x", "36");
  label.setAttribute("y", "41");
  label.textContent = "25";
  svg.append(label);
  return svg;
}

function updateClock(now) {
  if (!nodes || !run || (run.phase !== "play" && run.phase !== "preview")) return;
  const preview = run.phase === "preview";
  const left = preview ? Math.max(0, (run.phaseEndsAt - now) / 1000) : secondsLeft(run, now);
  const second = Math.ceil(left);
  if (second !== lastSecond) {
    lastSecond = second;
    nodes.seconds.textContent = String(second);
    nodes.live.textContent = preview ? `Starting in ${second}` : `${second} seconds`;
  }
  if (!preview && nodes.ringValue) {
    const remain = Math.max(0, run.phaseEndsAt - now);
    const frac = Math.min(1, remain / 25000);
    nodes.ringValue.style.strokeDashoffset = String(RING * (1 - frac));
    nodes.ringValue.classList.toggle("low", second <= 5);
  }
  nodes.judgingNote.hidden = !judging;
  if (run.phase === "play") {
    nodes.field.disabled = false;
    nodes.pass.disabled = false;
  }
}

function shake() {
  if (!nodes) return;
  nodes.field.classList.remove("bad");
  void nodes.field.offsetWidth;
  nodes.field.classList.add("bad");
  nodes.field.setAttribute("aria-invalid", "true");
}

function lock(hit, typed) {
  abortJudge();
  judging = false;
  run = lockAnswer(run, Date.now(), { ...hit, typed });
  renderPhase();
}

async function submitAnswer(raw) {
  if (!run || run.phase !== "play") return;
  const typed = raw.trim();
  if (!typed) return;
  const prompt = run.prompts[run.index];
  const compiled = answersFor(prompt);
  const norm = normalize(typed);
  const first = scoreAttempt(compiled, typed, { status: useJudge() ? "pending" : "off" });
  if (first.action === "lock") {
    lock(first.hit, typed);
    return;
  }
  if (!norm || !useJudge() || rejected.has(norm)) {
    shake();
    return;
  }
  abortJudge();
  const token = judgeToken;
  judgeAbort = new AbortController();
  judging = true;
  if (nodes) nodes.judgingNote.hidden = false;
  const result = await askJudge(prompt.id, typed, judgeAbort.signal);
  if (token !== judgeToken || !run || run.phase !== "play") return;
  judging = false;
  const decision = scoreAttempt(compiled, typed, result);
  if (decision.action === "lock") {
    lock(decision.hit, typed);
    return;
  }
  if (decision.remember && norm) rejected.add(norm);
  shake();
}

function renderReveal() {
  view = "reveal";
  nodes = null;
  abortJudge();
  const round = run.rounds[run.rounds.length - 1];
  const meta = round.tier ? tierMeta(round.tier) : null;
  const heading = round.kind === "hit" ? `${meta.label} · ${round.points}` : round.kind === "pass" ? "PASSED · 0" : "TIME · 0";
  const detail = el("div", { class: "reveal" }, [
    meter(),
    dots(),
    el("p", { class: `banner ${round.tier || "miss"}`, text: heading }),
  ]);
  if (round.kind === "hit") {
    detail.append(el("p", { class: "canonical", text: round.canonical }));
    if (round.judged) detail.append(el("p", { class: "ai", text: "Judged by AI" }));
    if (meta) detail.append(el("p", { class: "blurb", text: meta.blurb }));
  } else {
    detail.append(el("p", { class: "blurb", text: "That prompt scores zero. The ascent continues." }));
  }
  const examples = el("ul", { class: "examples" });
  for (const answer of round.examples || []) {
    const info = tierMeta(answer.tier);
    examples.append(el("li", {}, [`${info.label} · ${answer.name}`]));
  }
  if (examples.childNodes.length) {
    detail.append(el("p", { class: "examples-label", text: "Elsewhere on this prompt" }), examples);
  }
  const last = run.index + 1 >= run.prompts.length;
  detail.append(button(last ? "See the flight" : "Next prompt", "daily", () => {
    run = nextPrompt(run, Date.now());
    renderPhase();
  }));
  screen.replaceChildren(detail);
  screen.querySelector("button")?.focus();
}

function renderDone() {
  view = "done";
  nodes = null;
  const zone = zoneFor(run.altitude);
  const text = shareText({
    mode: run.mode,
    date: run.date,
    altitude: run.altitude,
    zone: zone.label,
    rounds: run.rounds,
  });
  const log = el("ol", { class: "log" });
  for (const round of run.rounds) {
    const mark = round.kind === "hit" ? `${tierMeta(round.tier).label} ${round.points}` : "0";
    const name = round.kind === "hit" ? round.canonical : round.kind === "pass" ? "Pass" : "Time";
    const extra = round.judged ? " · judged by AI" : "";
    log.append(el("li", {}, [el("span", { class: `swatch ${round.tier || "miss"}` }), `${name} · ${mark}${extra}`]));
  }
  const share = button("Copy result", "daily", async () => {
    const ok = await copyText(text);
    share.textContent = ok ? "Copied" : "Copy failed";
  });
  screen.replaceChildren(
    el("section", { class: "done" }, [
      el("p", { class: "eyebrow", text: run.mode === "daily" ? `DAILY · ${run.date}` : "UNLIMITED" }),
      el("h2", { class: "title", text: `${run.altitude} km` }),
      el("p", { class: "zone big", text: zone.label }),
      el("pre", { class: "share", text }),
      share,
      log,
      button("Back to the pad", "ghost", () => {
        run = null;
        showHome();
      }),
    ]),
  );
  screen.querySelector("button")?.focus();
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    const area = el("textarea", { class: "sr" });
    area.value = text;
    document.body.append(area);
    area.select();
    let ok = false;
    try {
      ok = document.execCommand("copy");
    } catch {
      ok = false;
    }
    area.remove();
    return ok;
  }
}

function frame() {
  // requestAnimationFrame's timestamp is time-since-navigation, not the clock
  // the engine stored with Date.now().
  const now = Date.now();
  if (run && (run.phase === "preview" || run.phase === "play")) {
    const before = run.phase;
    const ends = run.phaseEndsAt;
    run = tick(run, now);
    if (run.phase !== before) {
      if (before === "play") abortJudge();
      renderPhase();
    } else if (now >= ends && before === "preview") {
      renderPhase();
    } else {
      updateClock(now);
    }
  }
  requestAnimationFrame(frame);
}

async function boot() {
  showBoot("Opening the tower…");
  try {
    const [index, available] = await Promise.all([loadIndex(), probeJudge()]);
    bank = index;
    judgeOn = available;
    syncSettings();
    showHome();
  } catch {
    screen.replaceChildren(
      el("p", { class: "status", text: "The bank didn't load." }),
      button("Try again", "daily", () => boot()),
    );
  }
}

requestAnimationFrame(frame);
boot();
