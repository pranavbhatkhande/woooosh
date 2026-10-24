import { PLAY_MS, PREVIEW_MS, MAX_KM } from "./constants.js";
import { entryBlurb, sampleOthers, secondsLeft, shareText, totalKm } from "./engine.js";
import { formatDailyDate } from "./daily.js";
import { resultEmoji, tierMeta, zoneFor, zoneProgress } from "./tiers.js";

const LETTER = {
  pad: "P",
  ascent: "A",
  ceiling: "C",
  hotshot: "H",
  orbit: "O",
  apex: "X",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function rocket() {
  return `<svg class="mark" viewBox="0 0 16 16" aria-hidden="true">
    <rect width="16" height="16" fill="#07111f"/>
    <rect x="7" y="3" width="2" height="1" fill="#ff5a36"/>
    <rect x="6" y="4" width="4" height="1" fill="#ff5a36"/>
    <rect x="6" y="5" width="4" height="5" fill="#f4efe4"/>
    <rect x="7" y="6" width="2" height="2" fill="#7fd0ff"/>
    <rect x="5" y="8" width="1" height="3" fill="#ff5a36"/>
    <rect x="10" y="8" width="1" height="3" fill="#ff5a36"/>
    <rect x="7" y="10" width="2" height="1" fill="#ffd15c"/>
    <rect x="6" y="11" width="4" height="1" fill="#ff8a3d"/>
    <rect x="7" y="12" width="2" height="1" fill="#ff5a36"/>
  </svg>`;
}

function meter(km) {
  const zone = zoneFor(km);
  const width = Math.round(zoneProgress(km) * 1000) / 10;
  return `<div class="altimeter">
    <div class="alt-top">
      <span class="km">${km} km</span>
      <span class="zone">${escapeHtml(zone.label)}</span>
    </div>
    <div class="bar" role="meter" aria-label="Altitude" aria-valuemin="0" aria-valuemax="${MAX_KM}" aria-valuenow="${km}">
      <span class="bar-fill" style="width:${width}%"></span>
    </div>
  </div>`;
}

function dot(entry) {
  if (!entry || entry.outcome === "pending") {
    return `<li class="pending" title="Still ahead"><span class="sr">pending</span>·</li>`;
  }
  if (entry.outcome !== "hit" || !entry.answer) {
    return `<li class="miss" title="No score"><span class="sr">no score</span>–</li>`;
  }
  const tier = entry.answer.tier;
  const gem = entry.answer.gem;
  const letter = gem ? "G" : (LETTER[tier] || "?");
  const label = gem ? "Gem" : (tierMeta(tier)?.label || tier);
  return `<li class="${gem ? "gem" : escapeHtml(tier)}" title="${escapeHtml(label)}"><span class="sr">${escapeHtml(label)}</span>${letter}</li>`;
}

function dots(entries) {
  return `<ol class="dots" aria-label="Answers this run">${(entries || []).map(dot).join("")}</ol>`;
}

function ring(run, now) {
  const total = run.phase === "preview" ? PREVIEW_MS / 1000 : PLAY_MS / 1000;
  const left = secondsLeft(run, now);
  const radius = 36;
  const circ = 2 * Math.PI * radius;
  const offset = circ * (1 - Math.max(0, Math.min(1, left / total)));
  const shown = Math.ceil(left);
  return `<div class="ring">
    <svg viewBox="0 0 92 92" aria-hidden="true">
      <circle class="track" cx="46" cy="46" r="${radius}"></circle>
      <circle class="value" cx="46" cy="46" r="${radius}" stroke-dasharray="${circ.toFixed(2)}" stroke-dashoffset="${offset.toFixed(2)}"></circle>
    </svg>
    <div class="secs" id="secs">${shown}</div>
  </div>`;
}

export function patchTimer(run, now) {
  const secs = document.getElementById("secs");
  const value = document.querySelector(".ring .value");
  if (!secs || !value || !run) return;
  const total = run.phase === "preview" ? PREVIEW_MS / 1000 : PLAY_MS / 1000;
  const left = secondsLeft(run, now);
  const radius = 36;
  const circ = 2 * Math.PI * radius;
  value.setAttribute("stroke-dashoffset", (circ * (1 - Math.max(0, Math.min(1, left / total)))).toFixed(2));
  secs.textContent = String(Math.ceil(left));
}

function hud(run, km) {
  const mode = run.mode === "daily" ? `Daily · ${formatDailyDate(run.date)}` : "Unlimited";
  return `<header class="hud">
    <div class="hud-top"><span class="brand">WOOOOSH</span><span class="kicker">${escapeHtml(mode)}</span></div>
    ${meter(km)}
    ${dots(run.entries)}
  </header>`;
}

export function renderLoading(root) {
  root.innerHTML = `<section class="panel"><p class="kicker">Fueling</p><h1>WOOOOSH</h1><p>Loading the prompt bank.</p></section>`;
}

export function renderError(root, message) {
  root.innerHTML = `<section class="panel"><h1>WOOOOSH</h1><p class="error">${escapeHtml(message)}</p></section>`;
}

export function renderHome(root, { stats, bank, resume, today, already }) {
  const last = already ? stats.lastDailyResult : null;
  root.innerHTML = `<section class="home panel">
    ${rocket()}
    <p class="eyebrow">Launch</p>
    <h1>WOOOOSH</h1>
    <p class="tag">Seven prompts. Rarer answers climb higher.</p>
    <div class="actions">
      ${resume ? `<button type="button" id="resume" class="primary">Resume run</button>` : ""}
      <button type="button" id="daily" class="${resume ? "" : "primary"}">${already ? "Replay today's launch" : "Daily launch"}</button>
      <button type="button" id="unlimited">Unlimited</button>
      <button type="button" id="help" class="ghost">How altitude works</button>
    </div>
    ${last ? `<p class="hint">Today's grid is saved below. A replay does not extend the streak.</p>
      <pre class="grid">${escapeHtml(shareText(fakeRun(last), location.origin).split("\n").slice(0, 3).join("\n"))}</pre>` : ""}
    <dl class="stats">
      <div><dt>Streak</dt><dd>${stats.streak || 0}</dd></div>
      <div><dt>Best streak</dt><dd>${stats.bestStreak || 0}</dd></div>
      <div><dt>Best altitude</dt><dd>${stats.bestKm || 0} km</dd></div>
      <div><dt>Runs</dt><dd>${stats.runs || 0}</dd></div>
    </dl>
    <p class="hint">${bank.count} prompts in bank v${bank.version}. Daily for ${escapeHtml(formatDailyDate(today))} is the same seven for everyone.</p>
  </section>`;
}

function fakeRun(summary) {
  return summary;
}

export function renderHelp(root) {
  root.innerHTML = `<section class="help panel">
    <p class="eyebrow">Flight manual</p>
    <h1>How a launch works</h1>
    <p>Each run is seven prompts. You get a short look, then 25 seconds. Type one answer. The first answer in the bank locks in.</p>
    <ul>
      <li>A miss only shakes the box. Try again until the ring empties.</li>
      <li>Pass, or letting the clock run out, scores 0. The run still finishes all seven.</li>
      <li>Spelling is loose: case, accents, punctuation, a leading the/a/an, and simple plurals.</li>
      <li>One point is one kilometre. The rarer the answer, the higher you climb.</li>
    </ul>
    <h2>Tiers</h2>
    <div class="tiers">
      <div><span class="chip pad">P · Pad</span><span>5 km. Almost everyone says it.</span></div>
      <div><span class="chip ascent">A · Ascent</span><span>10 km. Familiar.</span></div>
      <div><span class="chip ceiling">C · Ceiling</span><span>25 km. A solid call.</span></div>
      <div><span class="chip hotshot">H · Hotshot</span><span>40 km. The clever pick that is not actually rare.</span></div>
      <div><span class="chip orbit">O · Orbit</span><span>60 km. Uncommon.</span></div>
      <div><span class="chip apex">X · Apex</span><span>100 km. Rare air.</span></div>
      <div><span class="chip gem">G · Gem</span><span>The one apex answer picked for the prompt.</span></div>
    </div>
    <p>Daily is one shared set per UTC day. Unlimited never repeats a prompt until you have seen the whole bank, then it starts again from the oldest.</p>
    <button type="button" id="home" class="primary">Back</button>
  </section>`;
}

export function renderRun(root, { run, now, draft }) {
  const km = totalKm(run);
  const prompt = run.prompts[run.index];
  const entry = run.entries[run.index];
  if (run.phase === "result") {
    root.innerHTML = `<section class="panel">${hud(run, km)}${resultBlock(prompt, entry, run.index, run.prompts.length)}</section>`;
    return;
  }
  const preview = run.phase === "preview";
  const reject = run.lastReject ? "Not in the bank. Try another." : "";
  root.innerHTML = `<section class="panel">
    ${hud(run, km)}
    <p class="count">Prompt ${run.index + 1} of ${run.prompts.length}</p>
    <h2 class="prompt" id="prompt">${escapeHtml(prompt?.text || "")}</h2>
    <p class="phase-note">${preview ? "Look first. Answers open in a moment." : "One answer. The first match locks in."}</p>
    <form id="answer-form" class="play">
      <div>
        <label class="sr" for="answer">Your answer</label>
        <input id="answer" name="answer" type="text" maxlength="80" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="done" ${preview ? "disabled" : ""} value="${escapeHtml(draft || "")}">
        <p class="reject" id="reject" role="status">${escapeHtml(reject)}</p>
        <div class="actions">
          <button type="submit" class="primary" ${preview ? "disabled" : ""}>Lock in</button>
          <button type="button" id="pass" class="ghost" ${preview ? "disabled" : ""}>Pass</button>
          <button type="button" id="home" class="ghost">Home</button>
        </div>
      </div>
      ${ring(run, now)}
    </form>
  </section>`;
}

function resultBlock(prompt, entry, index, total) {
  const last = index + 1 >= total;
  const answer = entry?.answer;
  const tier = answer?.tier;
  const gem = Boolean(answer?.gem);
  const chip = answer
    ? `<span class="chip ${gem ? "gem" : escapeHtml(tier)}">${gem ? "Gem" : escapeHtml(tierMeta(tier)?.label || "")} · ${answer.points} km</span>`
    : `<span class="chip miss">0 km</span>`;
  const samples = answer ? sampleOthers(prompt, answer.name) : sampleOthers(prompt, "");
  const rows = samples.map((sample) => {
    const meta = tierMeta(sample.tier);
    const mark = sample.gem ? "gem" : sample.tier;
    const label = sample.gem ? "Gem" : (meta?.label || sample.tier);
    const points = sample.gem ? 100 : (meta?.points || 0);
    return `<li><span><span class="chip ${escapeHtml(mark)}">${escapeHtml(label)}</span> ${escapeHtml(sample.name)}</span><span>${points}</span></li>`;
  }).join("");
  return `<p class="count">Prompt ${index + 1} of ${total}</p>
    <h2 class="prompt">${escapeHtml(prompt?.text || "")}</h2>
    <p class="result-head">${answer ? `<strong>${escapeHtml(answer.name)}</strong>` : "<strong>No score</strong>"} ${chip}</p>
    <p class="blurb">${escapeHtml(entryBlurb(entry))}</p>
    ${rows ? `<ul class="samples">${rows}</ul>` : ""}
    <div class="actions">
      <button type="button" id="next" class="primary">${last ? "Read the flight log" : "Next prompt"}</button>
      <button type="button" id="home" class="ghost">Home</button>
    </div>`;
}

export function renderDone(root, { run, copied }) {
  const km = totalKm(run);
  const zone = zoneFor(km);
  const text = shareText(run, location.origin);
  const rows = run.entries.map((entry, index) => {
    const icon = resultEmoji(entry);
    const name = entry.answer?.name || (entry.outcome === "pass" ? "Passed" : "Time");
    const points = entry.answer?.points || 0;
    return `<li><span>${icon} ${escapeHtml(entry.text)}</span><span>${escapeHtml(name)} · ${points}</span></li>`;
  }).join("");
  root.innerHTML = `<section class="panel">
    <p class="eyebrow">${run.mode === "daily" ? "Daily" : "Unlimited"}</p>
    <h1>${km} km</h1>
    <p class="tag">${escapeHtml(zone.label)}</p>
    ${meter(km)}
    ${dots(run.entries)}
    <pre class="grid" id="share-text">${escapeHtml(text)}</pre>
    <div class="actions">
      <button type="button" id="share" class="primary">${copied ? "Copied" : "Copy result"}</button>
      <button type="button" id="again">${run.mode === "daily" ? "Back to the pad" : "Another unlimited run"}</button>
      <button type="button" id="home" class="ghost">Home</button>
    </div>
    <ul class="log">${rows}</ul>
  </section>`;
}

export function setBankNote(bank) {
  const note = document.getElementById("bank-note");
  if (note && bank) note.textContent = `Prompt bank v${bank.version} · ${bank.count} prompts`;
}
