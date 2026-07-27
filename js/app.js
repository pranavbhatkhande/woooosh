import { LIFTS, PROGRAMS, DEFAULTS, programById, liftsUsed } from './programs.js';
import { resolveWorkout, completeWorkout, warmupSets, platesPerSide, roundToLoadable, epley1RM, liftHistory, sessionTonnage } from './engine.js';
import { load, save, freshState, exportJSON, importJSON } from './store.js';
import { lineChart, barChart } from './charts.js';

// #demo/<view> renders a seeded, non-persisting state for previews & screenshots
const DEMO = location.hash.startsWith('#demo');
let state = DEMO ? buildDemo() : load();
let view = (DEMO && location.hash.split('/')[1]) || 'today';
let summaryData = null;
let progressLift = null;
let progressMetric = 'weight';
let restTimer = { since: null, interval: null };

const $ = (s, el = document) => el.querySelector(s);
const app = $('#app');
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function buildDemo() {
  const d = DEFAULTS.lb;
  let s = freshState('novice-3', 'lb', d.start, d);
  const start = Date.now() - 70 * 86400000;
  for (let i = 0; i < 30; i++) {
    const w = resolveWorkout(s);
    const logged = {
      exercises: w.exercises.map((ex) => ({
        ...ex,
        setsDone: Array.from({ length: ex.sets }, (_, si) => {
          if (ex.amrap) return 6 + Math.floor(i / 6) + (si === 0 ? 1 : 0);
          // an occasional missed rep on the last set keeps the data honest
          return (i % 9 === 7 && si === ex.sets - 1) ? ex.reps - 1 : ex.reps;
        }),
      })),
    };
    const { next } = completeWorkout(s, logged);
    next.history.push({
      id: `demo${i}`,
      date: new Date(start + i * 2.33 * 86400000).toISOString(),
      programId: s.program.id,
      label: w.label,
      exercises: logged.exercises.map(({ lift, name, sets, reps, amrap, weight, tag, progresses, setsDone }) =>
        ({ lift, name, sets, reps, amrap, weight, tag, progresses, setsDone })),
    });
    s = next;
  }
  if (location.hash.includes('dark')) s.settings.theme = 'dark';
  if (location.hash.includes('active')) {
    const w = resolveWorkout(s);
    s.active = {
      date: new Date().toISOString(),
      programId: w.program.id,
      label: w.label,
      exercises: w.exercises.map((ex, i) => ({
        ...ex,
        setsDone: Array.from({ length: ex.sets }, (_, si) => (i === 0 ? (si < 2 ? 5 : si === 2 ? 3 : null) : null)),
      })),
    };
  }
  return s;
}

const fmtW = (w) => {
  const n = Math.round(w * 100) / 100;
  return Number.isInteger(n) ? String(n) : n.toFixed(n * 10 % 1 === 0 ? 1 : 2);
};
const unit = () => state.settings.units;
const persist = () => { if (!DEMO) save(state); };

function applyTheme() {
  const t = state?.settings?.theme || 'auto';
  if (t === 'auto') document.documentElement.removeAttribute('data-theme');
  else document.documentElement.setAttribute('data-theme', t);
}

/* ---------------- icons ---------------- */
const icons = {
  today: '<svg viewBox="0 0 24 24"><path d="M3 10.5h1.5v3H3zm16.5 0H21v3h-1.5zM6 7.5h2v9H6zm10 0h2v9h-2zM9 11h6v2H9z"/></svg>',
  programs: '<svg viewBox="0 0 24 24"><path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4zm2 2v11a1 1 0 0 0 1 1h9V7a1 1 0 0 0-1-1H7zm2 3h6v1.6H9V9zm0 3h6v1.6H9V12z"/></svg>',
  progress: '<svg viewBox="0 0 24 24"><path d="M4 19h16v1.6H4zM5 17l4.2-5.4 3.2 2.6L18 7.6l1.3 1L12.7 17l-3.3-2.6L6.3 18z"/></svg>',
  history: '<svg viewBox="0 0 24 24"><path d="M12 4a8 8 0 1 1-7.7 10.2l1.6-.5A6.4 6.4 0 1 0 5.6 12H8l-3.2 3.8L1.6 12h2.4A8 8 0 0 1 12 4zm-.8 3.5h1.6v4.2l3.4 2-.8 1.4-4.2-2.5z"/></svg>',
  settings: '<svg viewBox="0 0 24 24"><path d="M12 8.5A3.5 3.5 0 1 1 8.5 12 3.5 3.5 0 0 1 12 8.5zm0 1.6A1.9 1.9 0 1 0 13.9 12 1.9 1.9 0 0 0 12 10.1zM10.7 3h2.6l.5 2.1 1.4.6 1.9-1.1 1.8 1.8-1.1 1.9.6 1.4 2.1.5v2.6l-2.1.5-.6 1.4 1.1 1.9-1.8 1.8-1.9-1.1-1.4.6-.5 2.1h-2.6l-.5-2.1-1.4-.6-1.9 1.1-1.8-1.8 1.1-1.9-.6-1.4L3 13.3v-2.6l2.1-.5.6-1.4-1.1-1.9 1.8-1.8 1.9 1.1 1.4-.6z" fill-rule="evenodd"/></svg>',
  check: '<svg viewBox="0 0 24 24"><path d="M9.6 16.2 5.4 12l-1.4 1.4 5.6 5.6 10-10-1.4-1.4z"/></svg>',
};

/* ---------------- shell ---------------- */
function render() {
  applyTheme();
  if (!state) { renderOnboarding(); return; }
  const tabs = [
    ['today', 'Today'], ['programs', 'Programs'], ['progress', 'Progress'],
    ['history', 'History'], ['settings', 'Settings'],
  ];
  app.innerHTML = `
    <div class="shell">
      <nav class="nav" aria-label="Main">
        <div class="nav-brand"><span class="brand-mark">SS</span><span class="brand-name">Starting Strength</span></div>
        ${tabs.map(([id, label]) => `
          <button class="nav-btn ${view === id ? 'active' : ''}" data-nav="${id}" aria-label="${label}">
            <span class="nav-ic">${icons[id]}</span><span class="nav-label">${label}</span>
          </button>`).join('')}
      </nav>
      <main class="view" id="view"></main>
    </div>
    <div id="rest-pill" hidden></div>`;
  app.querySelectorAll('[data-nav]').forEach((b) =>
    b.addEventListener('click', () => { view = b.dataset.nav; summaryData = null; render(); }));
  ({ today: renderToday, programs: renderPrograms, progress: renderProgress, history: renderHistory, settings: renderSettings })[view]();
  updateRestPill();
}

/* ---------------- onboarding ---------------- */
let ob = { step: 0, units: 'lb', programId: 'novice-1', starts: null };

function renderOnboarding() {
  const d = DEFAULTS[ob.units];
  const steps = [obWelcome, obProgram, obWeights];
  app.innerHTML = `
    <div class="onboard">
      <div class="ob-card">
        <div class="ob-dots">${[0, 1, 2].map((i) => `<span class="dot ${i === ob.step ? 'on' : i < ob.step ? 'done' : ''}"></span>`).join('')}</div>
        ${steps[ob.step](d)}
      </div>
    </div>`;
  wireOnboarding();
}

function obWelcome() {
  return `
    <div class="ob-hero"><span class="brand-mark big">SS</span></div>
    <h1>Starting Strength</h1>
    <p class="ob-lede">Mark Rippetoe’s barbell programs — novice through advanced — with every workout computed for you and every rep tracked.</p>
    <div class="seg" role="radiogroup" aria-label="Units">
      <button class="seg-btn ${ob.units === 'lb' ? 'on' : ''}" data-units="lb">Pounds</button>
      <button class="seg-btn ${ob.units === 'kg' ? 'on' : ''}" data-units="kg">Kilograms</button>
    </div>
    <button class="btn primary block" data-next>Choose your program</button>`;
}

function obProgram() {
  return `
    <h1>Pick a program</h1>
    <p class="ob-lede">Never lifted on a program before? Start with Phase 1.</p>
    <div class="ob-programs">
      ${PROGRAMS.map((p) => `
        <button class="ob-prog ${ob.programId === p.id ? 'on' : ''}" data-prog="${p.id}">
          <span class="prog-level lv-${p.level.toLowerCase()}">${p.level}</span>
          <span class="prog-name">${esc(p.name)}</span>
          <span class="prog-blurb">${esc(p.blurb)}</span>
        </button>`).join('')}
    </div>
    <button class="btn primary block" data-next>Set starting weights</button>`;
}

function obWeights(d) {
  const program = programById(ob.programId);
  const lifts = liftsUsed(program);
  ob.starts = ob.starts || {};
  return `
    <h1>Starting weights</h1>
    <p class="ob-lede">Work-set weights for day one. When in doubt, start light — the bar goes up every session.</p>
    <div class="ob-weights">
      ${lifts.map((l) => `
        <label class="w-row">
          <span>${LIFTS[l].name}</span>
          <span class="w-input"><input type="number" inputmode="decimal" step="0.5" data-start="${l}"
            value="${ob.starts[l] ?? d.start[l] ?? d.bar}"><em>${ob.units}</em></span>
        </label>`).join('')}
    </div>
    <button class="btn primary block" data-finish>Start training</button>`;
}

function wireOnboarding() {
  app.querySelectorAll('[data-units]').forEach((b) => b.addEventListener('click', () => { ob.units = b.dataset.units; ob.starts = null; renderOnboarding(); }));
  app.querySelectorAll('[data-prog]').forEach((b) => b.addEventListener('click', () => { ob.programId = b.dataset.prog; ob.starts = null; renderOnboarding(); }));
  $('[data-next]')?.addEventListener('click', () => { ob.step++; renderOnboarding(); });
  $('[data-finish]')?.addEventListener('click', () => {
    const d = DEFAULTS[ob.units];
    const starts = {};
    app.querySelectorAll('[data-start]').forEach((inp) => {
      starts[inp.dataset.start] = Math.max(parseFloat(inp.value) || d.bar, d.bar);
    });
    state = freshState(ob.programId, ob.units, starts, d);
    persist();
    render();
  });
}

/* ---------------- today ---------------- */
function renderToday() {
  const v = $('#view');
  if (summaryData) { renderSummary(v); return; }
  if (state.active) { renderActiveWorkout(v); return; }

  const w = resolveWorkout(state);
  v.innerHTML = `
    <header class="view-head">
      <div>
        <p class="eyebrow">${esc(w.program.name)}</p>
        <h1>${esc(w.label)}</h1>
        <p class="sub">${new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</p>
      </div>
    </header>
    <section class="cards">
      ${w.exercises.map((ex) => `
        <article class="card preview">
          <div class="card-top">
            <span class="lift-chip s${LIFTS[ex.lift].slot}">${LIFTS[ex.lift].short}</span>
            <div class="card-title">
              <h2>${esc(ex.name)}</h2>
              ${ex.tag ? `<span class="tag">${esc(ex.tag)}</span>` : ''}
            </div>
            <div class="rx">${ex.amrap ? `${ex.sets}×<abbr title="as many reps as possible">max</abbr>` : `${ex.sets}×${ex.reps}`}</div>
          </div>
          ${ex.weight ? `<div class="big-weight">${fmtW(ex.weight)}<em>${unit()}</em></div>` : '<div class="big-weight bw">bodyweight</div>'}
        </article>`).join('')}
    </section>
    <button class="btn primary block" id="start-w">Start workout</button>`;
  $('#start-w').addEventListener('click', () => {
    state.active = {
      date: new Date().toISOString(),
      programId: w.program.id,
      label: w.label,
      exercises: w.exercises.map((ex) => ({ ...ex, setsDone: Array(ex.sets).fill(null) })),
    };
    persist();
    render();
  });
}

function renderActiveWorkout(v) {
  const a = state.active;
  const total = a.exercises.reduce((n, e) => n + e.sets, 0);
  const done = a.exercises.reduce((n, e) => n + e.setsDone.filter((r) => r != null).length, 0);
  v.innerHTML = `
    <header class="view-head">
      <div>
        <p class="eyebrow">${esc(programById(a.programId)?.name || '')}</p>
        <h1>${esc(a.label)}</h1>
        <p class="sub">${done} of ${total} sets logged</p>
      </div>
      <button class="btn ghost sm" id="cancel-w">Discard</button>
    </header>
    <div class="progress-rail"><div class="progress-fill" style="width:${total ? (done / total) * 100 : 0}%"></div></div>
    <section class="cards">
      ${a.exercises.map((ex, xi) => exerciseCard(ex, xi)).join('')}
    </section>
    <button class="btn primary block" id="finish-w" ${done === 0 ? 'disabled' : ''}>Finish workout</button>`;

  v.querySelectorAll('[data-set]').forEach((btn) => btn.addEventListener('click', () => {
    const [xi, si] = btn.dataset.set.split('.').map(Number);
    const ex = a.exercises[xi];
    const cur = ex.setsDone[si];
    if (ex.amrap) ex.setsDone[si] = cur == null ? 1 : cur >= 20 ? null : cur + 1;
    else ex.setsDone[si] = cur == null ? ex.reps : cur === 0 ? null : cur - 1;
    if (ex.setsDone[si] != null && (cur == null)) startRest();
    persist();
    render();
  }));
  v.querySelectorAll('[data-wadj]').forEach((btn) => btn.addEventListener('click', () => {
    const [xi, dir] = btn.dataset.wadj.split('.');
    const ex = a.exercises[+xi];
    const step = 2 * Math.min(...state.settings.plates);
    ex.weight = Math.max(state.settings.barWeight, ex.weight + (dir === 'up' ? step : -step));
    persist();
    render();
  }));
  v.querySelectorAll('[data-warm]').forEach((btn) => btn.addEventListener('click', () => {
    const el = $(`#warm-${btn.dataset.warm}`, v);
    el.hidden = !el.hidden;
    btn.classList.toggle('open', !el.hidden);
  }));
  $('#cancel-w').addEventListener('click', () => {
    if (confirm('Discard this workout? Logged sets will be lost.')) {
      state.active = null; persist(); stopRest(); render();
    }
  });
  $('#finish-w')?.addEventListener('click', finishWorkout);
}

function exerciseCard(ex, xi) {
  const plates = ex.weight ? platesPerSide(ex.weight, state.settings) : null;
  const warms = ex.weight ? warmupSets(ex.lift, ex.weight, state.settings) : [];
  return `
    <article class="card">
      <div class="card-top">
        <span class="lift-chip s${LIFTS[ex.lift].slot}">${LIFTS[ex.lift].short}</span>
        <div class="card-title">
          <h2>${esc(ex.name)}</h2>
          ${ex.tag ? `<span class="tag">${esc(ex.tag)}</span>` : ''}
        </div>
        <div class="rx">${ex.amrap ? `${ex.sets}×max` : `${ex.sets}×${ex.reps}`}</div>
      </div>
      ${ex.weight ? `
        <div class="weight-row">
          <button class="wadj" data-wadj="${xi}.dn" aria-label="decrease weight">−</button>
          <div class="big-weight">${fmtW(ex.weight)}<em>${unit()}</em></div>
          <button class="wadj" data-wadj="${xi}.up" aria-label="increase weight">+</button>
        </div>
        ${plates ? `<div class="plates">${plates.map((p) => `<span class="plate">${fmtW(p.plate)}${p.count > 1 ? `<i>×${p.count}</i>` : ''}</span>`).join('')}<span class="plates-note">per side</span></div>` : ''}
        ${warms.length ? `
          <button class="warm-toggle" data-warm="${xi}">Warm-up sets<svg viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg></button>
          <div class="warmups" id="warm-${xi}" hidden>
            ${warms.map((s) => `<span class="warm-set"><b>${fmtW(s.weight)}</b>×${s.reps}${s.times > 1 ? `×${s.times}` : ''}</span>`).join('')}
          </div>` : ''}` : ''}
      <div class="sets" role="group" aria-label="${esc(ex.name)} sets">
        ${ex.setsDone.map((r, si) => {
          const stateCls = r == null ? '' : (!ex.amrap && r >= ex.reps) ? 'hit' : ex.amrap && r > 0 ? 'hit' : 'part';
          return `<button class="set ${stateCls}" data-set="${xi}.${si}" aria-label="set ${si + 1}">
            ${r == null ? `<span class="set-ghost">${ex.amrap ? '+' : ex.reps}</span>` : r}
          </button>`;
        }).join('')}
      </div>
      ${ex.amrap ? '<p class="hint">Tap to count reps · tap past 20 to clear</p>' : ''}
    </article>`;
}

function finishWorkout() {
  const a = state.active;
  const { next, summary } = completeWorkout(state, a);
  next.history.push({
    id: `s${Date.now()}`,
    date: a.date,
    programId: a.programId,
    label: a.label,
    exercises: a.exercises.map(({ lift, name, sets, reps, amrap, weight, tag, progresses, setsDone }) =>
      ({ lift, name, sets, reps, amrap, weight, tag, progresses, setsDone })),
  });
  next.active = null;
  state = next;
  persist();
  stopRest();
  summaryData = { summary, session: state.history[state.history.length - 1] };
  render();
}

function renderSummary(v) {
  const { summary, session } = summaryData;
  const tonnage = sessionTonnage(session);
  v.innerHTML = `
    <div class="summary">
      <div class="summary-ic">${icons.check}</div>
      <h1>Workout logged</h1>
      <p class="sub">${esc(session.label)} · ${fmtW(tonnage)} ${unit()} total volume</p>
      <div class="cards">
        ${summary.length ? summary.map((s) => `
          <div class="sum-row">
            <span class="lift-chip s${LIFTS[s.lift].slot}">${LIFTS[s.lift].short}</span>
            <span class="sum-name">${LIFTS[s.lift].name}</span>
            <span class="sum-verdict ${s.kind}">
              ${s.kind === 'up' ? `↑ ${fmtW(s.to)} ${unit()} next` :
                s.kind === 'deload' ? `Deload → ${fmtW(s.to)} ${unit()}` :
                `Retry ${fmtW(s.to)} ${unit()} (${s.fails}/3)`}
            </span>
          </div>`).join('') : '<p class="hint">No progression changes this session.</p>'}
      </div>
      <button class="btn primary block" id="sum-done">Done</button>
    </div>`;
  $('#sum-done').addEventListener('click', () => { summaryData = null; render(); });
}

/* ---------------- rest timer ---------------- */
function startRest() {
  restTimer.since = Date.now();
  if (!restTimer.interval) restTimer.interval = setInterval(updateRestPill, 1000);
  updateRestPill();
}
function stopRest() {
  restTimer.since = null;
  clearInterval(restTimer.interval);
  restTimer.interval = null;
}
function updateRestPill() {
  const pill = $('#rest-pill');
  if (!pill) return;
  if (!restTimer.since || !state?.active) { pill.hidden = true; return; }
  const s = Math.floor((Date.now() - restTimer.since) / 1000);
  const mm = String(Math.floor(s / 60));
  const ss = String(s % 60).padStart(2, '0');
  pill.hidden = false;
  pill.className = s >= 180 ? 'ready' : '';
  pill.innerHTML = `<b>${mm}:${ss}</b><span>${s >= 180 ? 'Go — next set' : 'resting · 3–5 min'}</span>`;
  pill.onclick = stopRest;
}

/* ---------------- programs ---------------- */
let openProgram = null;
function renderPrograms() {
  const v = $('#view');
  const levels = ['Novice', 'Intermediate', 'Advanced'];
  v.innerHTML = `
    <header class="view-head"><div><h1>Programs</h1><p class="sub">Starting Strength & Practical Programming</p></div></header>
    ${levels.map((lv) => `
      <p class="group-label">${lv}</p>
      <section class="cards">
        ${PROGRAMS.filter((p) => p.level === lv).map((p) => programCard(p)).join('')}
      </section>`).join('')}`;
  v.querySelectorAll('[data-open]').forEach((b) => b.addEventListener('click', () => {
    openProgram = openProgram === b.dataset.open ? null : b.dataset.open;
    renderPrograms();
  }));
  v.querySelectorAll('[data-switch]').forEach((b) => b.addEventListener('click', (e) => {
    e.stopPropagation();
    switchProgram(b.dataset.switch);
  }));
}

function programCard(p) {
  const current = state.program.id === p.id;
  const open = openProgram === p.id;
  return `
    <article class="card prog ${open ? 'open' : ''}">
      <button class="prog-head" data-open="${p.id}">
        <div class="card-title">
          <h2>${esc(p.name)} ${current ? '<span class="current-pill">current</span>' : ''}</h2>
          <span class="sub">${esc(p.schedule)}</span>
        </div>
        <svg class="chev" viewBox="0 0 24 24"><path d="M7 10l5 5 5-5z"/></svg>
      </button>
      ${open ? `
        <div class="prog-body">
          <p>${esc(p.detail)}</p>
          ${p.days.map((d) => `
            <div class="day-line">
              <span class="day-label">${esc(d.label)}</span>
              <span class="day-lifts">${d.slots.map((s) => slotDesc(s)).join(' · ')}</span>
            </div>`).join('')}
          <p class="prog-progression"><b>Progression.</b> ${esc(p.progression)}</p>
          ${current ? '' : `<button class="btn primary block" data-switch="${p.id}">Switch to this program</button>`}
        </div>` : `<p class="prog-blurb-line">${esc(p.blurb)}</p>`}
    </article>`;
}

function slotDesc(s) {
  if (s.slot === 'alt') {
    return s.options.map((o) => `${LIFTS[o.lift].name} ${o.sets}×${o.reps}`).join(' / ');
  }
  const rx = s.amrap ? `${s.sets}×max` : `${s.sets}×${s.reps}`;
  const tag = s.slot === 'pct' ? ` @${Math.round(s.pct * 100)}%` : '';
  return `${LIFTS[s.lift].name} ${rx}${tag}`;
}

function switchProgram(id) {
  if (state.active && !confirm('Switching programs discards the workout in progress. Continue?')) return;
  const p = programById(id);
  const d = DEFAULTS[unit()];
  for (const l of liftsUsed(p)) {
    if (!state.lifts[l]) state.lifts[l] = { weight: d.start[l] ?? d.bar, increment: d.increment[l] ?? d.increment.press, fails: 0 };
  }
  state.program = { id, dayIndex: 0, alt: {}, startedAt: new Date().toISOString() };
  state.active = null;
  persist();
  openProgram = null;
  view = 'today';
  render();
}

/* ---------------- progress ---------------- */
function renderProgress() {
  const v = $('#view');
  const tracked = Object.keys(LIFTS).filter((l) => !LIFTS[l].bodyweight && liftHistory(state, l).length > 0);
  const available = tracked.length ? tracked : Object.keys(state.lifts);
  if (!progressLift || !available.includes(progressLift)) progressLift = available[0];
  const hist = liftHistory(state, progressLift);
  const cur = state.lifts[progressLift];
  const first = hist[0], last = hist[hist.length - 1];
  const bestE = hist.length ? Math.max(...hist.map((p) => p.e1rm)) : 0;

  v.innerHTML = `
    <header class="view-head"><div><h1>Progress</h1><p class="sub">${state.history.length} workouts logged</p></div></header>
    <div class="chips">
      ${available.map((l) => `<button class="chip ${l === progressLift ? 'on' : ''}" data-lift="${l}">
        <i class="swatch s${LIFTS[l].slot}"></i>${LIFTS[l].name}</button>`).join('')}
    </div>
    <section class="card pad">
      <div class="chart-head">
        <h2>${LIFTS[progressLift].name}</h2>
        <div class="seg mini">
          <button class="seg-btn ${progressMetric === 'weight' ? 'on' : ''}" data-metric="weight">Weight</button>
          <button class="seg-btn ${progressMetric === 'e1rm' ? 'on' : ''}" data-metric="e1rm">est. 1RM</button>
        </div>
      </div>
      <div class="stat-row">
        <div class="stat"><span class="stat-v">${cur ? fmtW(cur.weight) : '—'}</span><span class="stat-l">next work set</span></div>
        <div class="stat"><span class="stat-v ${last && first && last.weight > first.weight ? 'up' : ''}">${last && first ? `+${fmtW(last.weight - first.weight)}` : '—'}</span><span class="stat-l">gained ${unit()}</span></div>
        <div class="stat"><span class="stat-v">${bestE ? fmtW(Math.round(bestE)) : '—'}</span><span class="stat-l">best est. 1RM</span></div>
        <div class="stat"><span class="stat-v">${hist.length}</span><span class="stat-l">sessions</span></div>
      </div>
      <div id="chart-lift"></div>
    </section>
    <section class="card pad">
      <div class="chart-head"><h2>All lifts</h2></div>
      <div class="legend" id="legend-all"></div>
      <div id="chart-all"></div>
    </section>
    <section class="card pad">
      <div class="chart-head"><h2>Weekly volume</h2><span class="sub">${unit()} lifted</span></div>
      <div id="chart-vol"></div>
    </section>`;

  v.querySelectorAll('[data-lift]').forEach((b) => b.addEventListener('click', () => { progressLift = b.dataset.lift; renderProgress(); }));
  v.querySelectorAll('[data-metric]').forEach((b) => b.addEventListener('click', () => { progressMetric = b.dataset.metric; renderProgress(); }));

  const css = getComputedStyle(document.documentElement);
  const slotColor = (n) => css.getPropertyValue(`--s${n}`).trim();

  lineChart($('#chart-lift'), {
    series: [{
      name: '',
      color: slotColor(LIFTS[progressLift].slot),
      points: hist.map((p) => ({ t: +new Date(p.date), y: progressMetric === 'weight' ? p.weight : Math.round(p.e1rm) })),
    }],
    yFmt: (val) => `${fmtW(Math.round(val))}`,
  });

  const allSeries = Object.keys(LIFTS)
    .filter((l) => !LIFTS[l].bodyweight)
    .map((l) => ({ lift: l, pts: liftHistory(state, l) }))
    .filter((s) => s.pts.length > 0)
    .map((s) => ({
      name: LIFTS[s.lift].name,
      color: slotColor(LIFTS[s.lift].slot),
      points: s.pts.map((p) => ({ t: +new Date(p.date), y: p.weight })),
    }));
  $('#legend-all').innerHTML = allSeries.map((s) => `<span class="lg"><i style="background:${s.color}"></i>${s.name}</span>`).join('');
  lineChart($('#chart-all'), { series: allSeries, yFmt: (val) => fmtW(Math.round(val)), height: 260 });

  const weeks = new Map();
  for (const s of state.history) {
    const d = new Date(s.date);
    const monday = new Date(d);
    monday.setDate(d.getDate() - ((d.getDay() + 6) % 7));
    const key = monday.toISOString().slice(0, 10);
    weeks.set(key, (weeks.get(key) || 0) + sessionTonnage(s));
  }
  const bars = [...weeks.entries()].sort().slice(-12).map(([k, y]) => ({
    label: new Date(k).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }), y: Math.round(y),
  }));
  barChart($('#chart-vol'), { bars, yFmt: (val) => val >= 1000 ? `${(val / 1000).toFixed(1)}k` : String(Math.round(val)) });
}

/* ---------------- history ---------------- */
let openSession = null;
function renderHistory() {
  const v = $('#view');
  const sessions = [...state.history].reverse();
  const groups = new Map();
  for (const s of sessions) {
    const key = new Date(s.date).toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(s);
  }
  v.innerHTML = `
    <header class="view-head"><div><h1>History</h1><p class="sub">${sessions.length} workouts</p></div></header>
    ${sessions.length === 0 ? '<div class="empty">Your training log is empty. Finish a workout and it lands here.</div>' : ''}
    ${[...groups.entries()].map(([month, list]) => `
      <p class="group-label">${month}</p>
      <section class="cards">
        ${list.map((s) => sessionCard(s)).join('')}
      </section>`).join('')}`;
  v.querySelectorAll('[data-sess]').forEach((b) => b.addEventListener('click', () => {
    openSession = openSession === b.dataset.sess ? null : b.dataset.sess;
    renderHistory();
  }));
  v.querySelectorAll('[data-del]').forEach((b) => b.addEventListener('click', (e) => {
    e.stopPropagation();
    if (!confirm('Delete this session from the log? Current work weights are not affected.')) return;
    state.history = state.history.filter((s) => s.id !== b.dataset.del);
    persist();
    renderHistory();
  }));
}

function sessionCard(s) {
  const open = openSession === s.id;
  const d = new Date(s.date);
  return `
    <article class="card sess ${open ? 'open' : ''}">
      <button class="sess-head" data-sess="${s.id}">
        <div class="sess-date"><b>${d.getDate()}</b><span>${d.toLocaleDateString(undefined, { weekday: 'short' })}</span></div>
        <div class="card-title">
          <h2>${esc(s.label)}</h2>
          <span class="sub">${s.exercises.map((e) => LIFTS[e.lift].short).join(' · ')}</span>
        </div>
        <span class="sess-vol">${fmtW(Math.round(sessionTonnage(s)))} ${unit()}</span>
      </button>
      ${open ? `
        <div class="sess-body">
          <table class="sess-table">
            ${s.exercises.map((e) => `
              <tr>
                <td><span class="lift-chip s${LIFTS[e.lift].slot}">${LIFTS[e.lift].short}</span> ${esc(e.name)}</td>
                <td class="num">${e.weight ? `${fmtW(e.weight)} ${unit()}` : 'BW'}</td>
                <td class="num">${e.setsDone.map((r) => r == null ? '·' : r).join(' / ')}</td>
              </tr>`).join('')}
          </table>
          <button class="btn ghost sm danger" data-del="${s.id}">Delete session</button>
        </div>` : ''}
    </article>`;
}

/* ---------------- settings ---------------- */
function renderSettings() {
  const v = $('#view');
  const s = state.settings;
  v.innerHTML = `
    <header class="view-head"><div><h1>Settings</h1></div></header>
    <section class="card pad">
      <h2 class="set-h">Units & bar</h2>
      <div class="set-row"><span>Units</span>
        <div class="seg mini">
          <button class="seg-btn ${s.units === 'lb' ? 'on' : ''}" data-set-units="lb">lb</button>
          <button class="seg-btn ${s.units === 'kg' ? 'on' : ''}" data-set-units="kg">kg</button>
        </div>
      </div>
      <div class="set-row"><span>Bar weight</span>
        <span class="w-input"><input type="number" inputmode="decimal" id="set-bar" value="${s.barWeight}"><em>${s.units}</em></span>
      </div>
      <div class="set-row col"><span>Plate pairs available</span>
        <input type="text" id="set-plates" value="${s.plates.join(', ')}" spellcheck="false">
      </div>
    </section>
    <section class="card pad">
      <h2 class="set-h">Work weights & jumps</h2>
      ${Object.entries(state.lifts).map(([l, rec]) => `
        <div class="set-row">
          <span><span class="lift-chip s${LIFTS[l].slot}">${LIFTS[l].short}</span> ${LIFTS[l].name}</span>
          <span class="lift-edit">
            <span class="w-input"><input type="number" inputmode="decimal" step="0.5" data-lw="${l}" value="${rec.weight}"><em>${s.units}</em></span>
            <span class="w-input plus"><input type="number" inputmode="decimal" step="0.5" data-li="${l}" value="${rec.increment}"><em>+/session</em></span>
          </span>
        </div>`).join('')}
    </section>
    <section class="card pad">
      <h2 class="set-h">Appearance</h2>
      <div class="set-row"><span>Theme</span>
        <div class="seg mini">
          ${['auto', 'light', 'dark'].map((t) => `<button class="seg-btn ${s.theme === t ? 'on' : ''}" data-theme-set="${t}">${t}</button>`).join('')}
        </div>
      </div>
    </section>
    <section class="card pad">
      <h2 class="set-h">Data</h2>
      <div class="btn-row">
        <button class="btn ghost" id="exp">Export backup</button>
        <button class="btn ghost" id="imp">Import backup</button>
      </div>
      <input type="file" id="imp-file" accept=".json,application/json" hidden>
      <button class="btn ghost danger block" id="reset">Erase everything</button>
    </section>
    <p class="colophon">Programs from <i>Starting Strength: Basic Barbell Training</i> and <i>Practical Programming for Strength Training</i> by Mark Rippetoe. This app is an unofficial training log.</p>`;

  v.querySelectorAll('[data-set-units]').forEach((b) => b.addEventListener('click', () => {
    const to = b.dataset.setUnits;
    if (to === s.units) return;
    convertUnits(to);
    renderSettings();
  }));
  $('#set-bar').addEventListener('change', (e) => {
    s.barWeight = parseFloat(e.target.value) || s.barWeight; persist();
  });
  $('#set-plates').addEventListener('change', (e) => {
    const plates = e.target.value.split(/[,\s]+/).map(parseFloat).filter((n) => n > 0);
    if (plates.length) { s.plates = plates.sort((a, b) => b - a); persist(); }
    renderSettings();
  });
  v.querySelectorAll('[data-lw]').forEach((inp) => inp.addEventListener('change', () => {
    const n = parseFloat(inp.value);
    if (n > 0) { state.lifts[inp.dataset.lw].weight = n; persist(); }
  }));
  v.querySelectorAll('[data-li]').forEach((inp) => inp.addEventListener('change', () => {
    const n = parseFloat(inp.value);
    if (n > 0) { state.lifts[inp.dataset.li].increment = n; persist(); }
  }));
  v.querySelectorAll('[data-theme-set]').forEach((b) => b.addEventListener('click', () => {
    s.theme = b.dataset.themeSet; persist(); applyTheme(); renderSettings();
  }));
  $('#exp').addEventListener('click', () => exportJSON(state));
  $('#imp').addEventListener('click', () => $('#imp-file').click());
  $('#imp-file').addEventListener('change', async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    try {
      state = await importJSON(f);
      persist();
      render();
    } catch (err) {
      alert(`Import failed: ${err.message}`);
    }
  });
  $('#reset').addEventListener('click', () => {
    if (!confirm('Erase all programs, weights, and history? This cannot be undone.')) return;
    if (!confirm('Really erase everything?')) return;
    localStorage.clear();
    state = null;
    ob = { step: 0, units: 'lb', programId: 'novice-1', starts: null };
    render();
  });
}

function convertUnits(to) {
  const k = to === 'kg' ? 0.45359237 : 1 / 0.45359237;
  const d = DEFAULTS[to];
  const s = state.settings;
  s.units = to;
  s.barWeight = d.bar;
  s.plates = [...d.plates];
  const snap = (w) => Math.max(Math.round((w * k) / 0.25) * 0.25, d.bar);
  for (const rec of Object.values(state.lifts)) {
    rec.weight = snap(rec.weight);
    rec.increment = Math.max(Math.round((rec.increment * k) / 0.25) * 0.25, 0.25);
  }
  persist();
}

/* ---------------- boot ---------------- */
window.addEventListener('resize', () => {
  if (view === 'progress' && state && !document.hidden) renderProgress();
});
if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  navigator.serviceWorker.register('./sw.js').catch(() => {});
}
render();
