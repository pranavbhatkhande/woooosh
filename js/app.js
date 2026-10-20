import {
  adjustmentNote,
  adjustments,
  bigIdea,
  compliance,
  complianceNote,
  complianceRule,
  doctorIntro,
  doctorItems,
  flatDisclosure,
  grocery,
  grades,
  heartRateNote,
  labs,
  labsNote,
  levers,
  lifestyle,
  meals,
  metabolism,
  metabolismIntro,
  myths,
  nav,
  nutritionTargets,
  outcome,
  outcomes,
  personalize,
  phases,
  plate,
  plateNote,
  principles,
  profile,
  progressionRule,
  references,
  sampleDay,
  sessionIntro,
  sessionMeta,
  sessions,
  sleepFindings,
  sleepRoutine,
  supplementNote,
  supplements,
  templates,
  trackingMetrics,
  trendCopy,
  vascularNote,
  volumeNote,
  weeklyFood,
} from "./data.js";
import {
  CM_PER_IN,
  computeTargets,
  fromKg,
  phaseIndexForWeek,
  toKg,
  trendWindow,
} from "./logic.js";

const STORAGE_PREFS = "woooosh.recomp.prefs";
const STORAGE_LOG = "woooosh.recomp.checkins";
const memory = new Map();

const main = document.querySelector("#main");
const navEl = document.querySelector("#nav");
const themeBtn = document.querySelector("#theme");

let banner = "";
let preserveScroll = false;

function storageGet(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return memory.has(key) ? memory.get(key) : null;
  }
}

function storageSet(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    memory.set(key, value);
  }
}

function loadPrefs() {
  const defaults = {
    unit: "kg",
    waistUnit: "cm",
    sex: "unspecified",
    bodyComp: "unsure",
    activity: "standard",
    weight: "",
    goalWeight: "",
    maintenance: "",
    template: "A",
    week: 1,
    theme: "system",
  };
  try {
    const saved = JSON.parse(storageGet(STORAGE_PREFS) || "{}");
    return { ...defaults, ...saved };
  } catch {
    return defaults;
  }
}

function loadLog() {
  try {
    const rows = JSON.parse(storageGet(STORAGE_LOG) || "[]");
    return Array.isArray(rows) ? rows.filter((row) => row && row.date && row.weight > 0) : [];
  } catch {
    return [];
  }
}

let prefs = loadPrefs();
let checkins = loadLog();

function savePrefs() {
  storageSet(STORAGE_PREFS, JSON.stringify(prefs));
}

function saveLog() {
  storageSet(STORAGE_LOG, JSON.stringify(checkins));
}

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2).toLowerCase(), value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  for (const child of children) {
    if (child == null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

const anchorSection = {
  levers: "plan",
  keep: "plan",
  weekglance: "plan",
  doctor: "plan",
  personalize: "plan",
  templates: "train",
  "this-week": "train",
  sessions: "train",
  progression: "train",
  calculator: "eat",
  targets: "eat",
  plate: "eat",
  meals: "eat",
  sample: "eat",
  grocery: "eat",
  flex: "eat",
  findings: "sleep",
  routine: "sleep",
  lifestyle: "sleep",
  checkin: "track",
  trend: "track",
  log: "track",
  good: "track",
  outcomes: "track",
  adjust: "track",
  labs: "track",
};

function parseHash() {
  const raw = decodeURIComponent((location.hash || "#plan").replace(/^#/, ""));
  const known = new Set(nav.map((item) => item.id));
  if (known.has(raw)) return { section: raw, anchor: null };
  if (/^ref-\d+$/.test(raw)) return { section: "references", anchor: raw };
  if (anchorSection[raw]) return { section: anchorSection[raw], anchor: raw };
  const [section, anchor] = raw.split("/");
  if (known.has(section)) return { section, anchor: anchor || null };
  return { section: "plan", anchor: null };
}

function go(hash) {
  const next = hash.startsWith("#") ? hash : `#${hash}`;
  if (location.hash === next) render();
  else location.hash = next;
}

function rich(text) {
  const frag = document.createDocumentFragment();
  const re = /\[(\d+(?:\s*,\s*\d+)*)\]/g;
  let last = 0;
  let match;
  while ((match = re.exec(text))) {
    if (match.index > last) frag.append(text.slice(last, match.index));
    const nums = match[1].split(/\s*,\s*/);
    frag.append("[");
    nums.forEach((num, index) => {
      if (index) frag.append(", ");
      frag.append(el("a", {
        href: `#ref-${num}`,
        class: "cite",
        dataset: { ref: num },
      }, [num]));
    });
    frag.append("]");
    last = match.index + match[0].length;
  }
  if (last < text.length) frag.append(text.slice(last));
  return frag;
}

function p(text, className) {
  return el("p", { class: className || "" }, [rich(text)]);
}

function h2(text, id) {
  return el("h2", { id }, [text]);
}

function block(id, title, ...nodes) {
  return el("section", { class: "block", id }, [h2(title, id ? `${id}-title` : null), ...nodes]);
}

function jumps(links) {
  return el("nav", { class: "jumps", "aria-label": "On this page" }, links.map(([id, label]) => (
    el("a", { href: `#${id}` }, [label])
  )));
}

function stack(headers, rows) {
  const wrap = el("div", { class: "stack" });
  rows.forEach((row) => {
    const card = el("article", { class: "kv" });
    headers.forEach((header, index) => {
      if (row[index] == null || row[index] === "") return;
      card.append(el("div", { class: "kv-row" }, [
        el("div", { class: "k" }, [header]),
        el("div", { class: "v" }, [rich(String(row[index]))]),
      ]));
    });
    wrap.append(card);
  });
  return wrap;
}

function fmt(n, digits) {
  return Number(n).toLocaleString(undefined, {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  });
}

function todayISO() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function formatDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

function applyTheme() {
  if (prefs.theme === "light" || prefs.theme === "dark") {
    document.documentElement.dataset.theme = prefs.theme;
  } else {
    delete document.documentElement.dataset.theme;
  }
  const dark = prefs.theme === "dark" || (
    prefs.theme !== "light" && window.matchMedia("(prefers-color-scheme: dark)").matches
  );
  themeBtn.textContent = dark ? "Light" : "Dark";
  themeBtn.setAttribute("aria-pressed", dark ? "true" : "false");
}

function renderNav(current) {
  navEl.replaceChildren(...nav.map((item) => el("a", {
    href: `#${item.id}`,
    "aria-current": item.id === current ? "page" : null,
  }, [item.label])));
}

function templateById(id) {
  return templates.find((item) => item.id === id) || templates[0];
}

function renderPlan() {
  const template = templateById(prefs.template);
  const phase = phases[phaseIndexForWeek(prefs.week)] || phases[1];
  return el("div", {}, [
    el("p", { class: "eyebrow" }, ["Coach’s summary"]),
    el("h1", {}, ["Lift heavy, do genuinely hard cardio, walk a lot, eat a modest deficit with plenty of protein, and protect your sleep."]),
    el("p", { class: "meta" }, [`${profile.prepared} · ${profile.date}`]),
    p(profile.line, "lede"),
    p(bigIdea),
    el("div", { class: "stats" }, [
      stat("−5 to −8%", "Body weight in 12 weeks at ~85% adherence"),
      stat("~+5 mL/kg/min", "Average VO2max change, about 1.5 METs"),
      stat("A few mmHg", "Resting blood pressure, if the habits stick"),
      stat("16–24 wk", "Usual timeline for the 10% end of the goal"),
    ]),
    p(outcome),
    el("div", { class: "actions" }, [
      el("a", { class: "button", href: "#eat" }, ["Set protein and calories"]),
      el("a", { class: "button secondary", href: "#train" }, ["Pick a training week"]),
      el("a", { class: "button secondary", href: "#track" }, ["Log a check-in"]),
    ]),
    block("levers", "80/20 levers, ranked by impact", ...levers.map(leverCard)),
    block("keep", "What to hit, and what can flex",
      p(complianceNote),
      el("div", { class: "stack" }, compliance.map((row) => el("article", { class: "kv" }, [
        el("h3", {}, [row.tier]),
        p(row.behaviors),
        el("p", { class: "fine" }, [row.why]),
      ]))),
      p(complianceRule, "fine"),
    ),
    block("weekglance", "This week",
      p(`Template ${template.id}, ${template.name} (${template.time}). Week ${prefs.week}: ${phase.name}. ${phase.lifting}`),
      el("p", {}, [
        el("a", { href: "#templates" }, ["Change template or week"]),
      ]),
    ),
    block("doctor", "Check with a doctor first if…",
      p(doctorIntro),
      el("ul", { class: "list" }, doctorItems.map((item) => el("li", {}, [rich(item)]))),
    ),
    block("personalize", "What to personalize first",
      stack(["Input", "Why it matters", "What to do"], personalize),
    ),
    details("What “metabolism” actually is", [
      p(metabolismIntro),
      stack(["Component", "What it is", "What changes it", "Realistic change", "Evidence"], metabolism),
    ]),
    details("Myths and overhyped claims", [
      stack(["Claim", "Verdict", "Evidence"], myths),
    ]),
    p(grades, "fine"),
  ]);
}

function stat(value, label) {
  return el("div", { class: "stat" }, [
    el("div", { class: "stat-v" }, [value]),
    el("div", { class: "stat-l" }, [label]),
  ]);
}

function leverCard(lever) {
  return el("article", { class: "lever" }, [
    el("div", { class: "num", "aria-hidden": "true" }, [String(lever.n)]),
    el("div", {}, [
      el("h3", {}, [lever.name]),
      p(lever.target),
      el("p", { class: "tags" }, [
        el("span", { class: "tag" }, [lever.evidence]),
        el("span", { class: "tag" }, [rich(lever.impact)]),
        el("span", { class: "tag quiet" }, [rich(`[${lever.cites}]`)]),
      ]),
    ]),
  ]);
}

function details(summary, nodes) {
  return el("details", { class: "fold" }, [
    el("summary", {}, [summary]),
    ...nodes,
  ]);
}

function renderTrain() {
  const template = templateById(prefs.template);
  const phaseIdx = phaseIndexForWeek(prefs.week);
  const phase = phases[phaseIdx] || phases[1];
  return el("div", {}, [
    el("p", { class: "eyebrow" }, ["Training · 4–5 h/week"]),
    el("h1", {}, ["Three ways to spend the week"]),
    p("Pick one template and switch freely. Wall sits are the blood-pressure finisher: 4×2 min, about 2 min rest, three days a week."),
    jumps([["templates", "Templates"], ["this-week", "This week"], ["sessions", "Sessions"], ["progression", "12 weeks"]]),
    block("templates", "Weekly template",
      el("div", { class: "choices", role: "radiogroup", "aria-label": "Training template" }, templates.map((item) => (
        el("button", {
          type: "button",
          class: item.id === template.id ? "choice on" : "choice",
          "aria-pressed": item.id === template.id ? "true" : "false",
          onclick: () => {
            prefs.template = item.id;
            savePrefs();
            rerender();
          },
        }, [
          el("span", { class: "choice-k" }, [`${item.id} · ${item.role}`]),
          el("span", { class: "choice-t" }, [item.name]),
          el("span", { class: "choice-s" }, [item.time]),
        ])
      ))),
      p(template.blurb),
      stack(["Day", "Session", "Duration", "Notes"], template.days),
    ),
    block("this-week", "Where you are in the 12 weeks", weekControl()),
    block("sessions", "Sample sessions",
      p(sessionIntro),
      ...["A", "B", "C"].map((id) => details(`${sessionMeta[id].title} — ${sessionMeta[id].focus}`, [
        stack(["Exercise", "Sets × reps", "RPE", "Substitutions"], sessions[id]),
      ])),
      p(volumeNote),
      p(vascularNote),
    ),
    block("progression", "12-week progression",
      stack(["Weeks", "Phase", "Lifting", "Intervals", "Steps"], phases.map((row, index) => [
        row.weeks,
        `${row.name}${index === phaseIdx ? " · you are here" : ""}`,
        row.lifting,
        row.intervals,
        row.steps,
      ])),
      h3("Progression rule"),
      p(progressionRule),
      h3("Heart rate"),
      p(heartRateNote),
    ),
    details("Dose and evidence", [
      stack(["Recommendation", "Dose", "Evidence", "Impact", "Sources"], principles),
    ]),
  ]);
}

function weekLabel(week) {
  const row = phases[phaseIndexForWeek(week)] || phases[1];
  return `Week ${week} · ${row.weeks} · ${row.name}`;
}

function weekControl() {
  const input = el("input", {
    type: "range",
    min: "0",
    max: "12",
    step: "1",
    value: String(prefs.week),
    "aria-labelledby": "week-label",
  });
  const label = el("p", { class: "week-label" }, [weekLabel(prefs.week)]);
  const detail = el("div", {});
  const paint = (week) => {
    const row = phases[phaseIndexForWeek(week)] || phases[1];
    input.setAttribute("aria-valuenow", String(week));
    input.setAttribute("aria-label", `Week ${week}`);
    label.textContent = weekLabel(week);
    detail.replaceChildren(stack(
      ["Focus", "Plan"],
      [["Lifting", row.lifting], ["Intervals", row.intervals], ["Steps", row.steps]],
    ));
  };
  input.addEventListener("input", () => {
    prefs.week = Number(input.value);
    savePrefs();
    paint(prefs.week);
  });
  paint(prefs.week);
  return el("div", { class: "field" }, [
    el("span", { class: "field-l", id: "week-label" }, ["Week"]),
    input,
    label,
    detail,
  ]);
}

function h3(text) {
  return el("h3", {}, [text]);
}

function field(label, control, hint) {
  return el("label", { class: "field" }, [
    el("span", { class: "field-l" }, [label]),
    control,
    hint ? el("span", { class: "fine" }, [hint]) : null,
  ]);
}

function choiceGroup(name, label, options, current, onChange) {
  return el("fieldset", { class: "field" }, [
    el("legend", {}, [label]),
    el("div", { class: "pills" }, options.map(([value, text]) => (
      el("label", { class: value === current ? "pill on" : "pill" }, [
        el("input", {
          type: "radio",
          name,
          value,
          checked: value === current,
          onchange: () => onChange(value),
        }),
        text,
      ])
    ))),
  ]);
}

function renderEat() {
  const root = el("div", {}, [
    el("p", { class: "eyebrow" }, ["Nutrition"]),
    el("h1", {}, ["Protein, a modest deficit, and a plate you can repeat"]),
    p("The plan does not publish a calorie equation by sex or activity. Protein is 1.6–2.2 g/kg, the loss rate is 0.5–0.7% of body weight per week, and intake is maintenance minus 300–500 kcal/day. Sex changes portion size and week-to-week weight noise. Activity chooses the training template. Your scale trend is the calibration."),
    jumps([["calculator", "Calculator"], ["plate", "Plate"], ["sample", "Sample day"], ["grocery", "Grocery"]]),
  ]);
  const results = el("div", { class: "results", "aria-live": "polite" });
  const form = el("form", { class: "card", id: "calculator" }, [
    el("h2", {}, ["Targets from your weight"]),
    choiceGroup("unit", "Weight unit", [["kg", "Kilograms"], ["lb", "Pounds"]], prefs.unit, (value) => {
      prefs.unit = value;
      savePrefs();
      const weight = document.querySelector("#calculator [name='weight']");
      if (weight) weight.placeholder = value === "lb" ? "e.g. 176" : "e.g. 80";
      const goal = document.querySelector("#calculator [name='goal']");
      if (goal) goal.placeholder = value === "lb" ? "e.g. 160" : "e.g. 72";
      paintResults();
    }),
    field("Body weight", el("input", {
      inputmode: "decimal",
      name: "weight",
      value: prefs.weight,
      autocomplete: "off",
      placeholder: prefs.unit === "lb" ? "e.g. 176" : "e.g. 80",
      oninput: (event) => {
        prefs.weight = event.target.value;
        savePrefs();
        paintResults();
      },
    })),
    choiceGroup("sex", "Sex", [["unspecified", "Not set"], ["female", "Female"], ["male", "Male"]], prefs.sex, (value) => {
      prefs.sex = value;
      savePrefs();
      paintResults();
    }),
    choiceGroup("body", "Which end of the range", [
      ["unsure", "Not sure"],
      ["higher-fat", "A lot of fat to lose"],
      ["lean", "Already fairly lean"],
    ], prefs.bodyComp, (value) => {
      prefs.bodyComp = value;
      savePrefs();
      rerender();
    }),
    prefs.bodyComp === "higher-fat"
      ? field("Goal weight", el("input", {
        inputmode: "decimal",
        name: "goal",
        value: prefs.goalWeight,
        placeholder: prefs.unit === "lb" ? "e.g. 160" : "e.g. 72",
        oninput: (event) => {
          prefs.goalWeight = event.target.value;
          savePrefs();
          paintResults();
        },
      }), "Protein uses goal weight in this case. The weekly loss rate still uses current weight.")
      : null,
    choiceGroup("activity", "Time you can train", [
      ["standard", "About 4–5 h/week"],
      ["busy", "Busy week, about 2 h"],
    ], prefs.activity, (value) => {
      prefs.activity = value;
      savePrefs();
      paintResults();
    }),
    field("Maintenance intake, if you know it", el("input", {
      inputmode: "numeric",
      name: "maintenance",
      value: prefs.maintenance,
      placeholder: "kcal/day, optional",
      oninput: (event) => {
        prefs.maintenance = event.target.value;
        savePrefs();
        paintResults();
      },
    }), "Log usual intake for 7–14 days, or type an estimate. Leave blank to see only the deficit and the loss rate."),
  ]);
  form.addEventListener("submit", (event) => event.preventDefault());

  function paintResults() {
    results.replaceChildren(resultCard(computeTargets(prefs)));
  }
  paintResults();
  root.append(
    form,
    results,
    block("targets", "The ranges behind the numbers",
      stack(["Target", "Dose", "Evidence", "Impact", "Notes"], nutritionTargets),
    ),
    block("plate", "Plate method, if you don’t want to log",
      p("Use this instead of numbers if tracking makes you anxious. The plan says to adjust by the weight trend, not by feel."),
      stack(["Plate part", "Portion", "Examples"], plate),
      p(plateNote),
    ),
    block("meals", "A week of default meals",
      stack(["Slot", "Default", "Protein anchor"], meals),
      p(weeklyFood),
    ),
    block("sample", "Sample day",
      p(sampleDay.intro),
      stack(["Meal", "Food", "Protein"], sampleDay.rows),
      p(sampleDay.total),
      p("The calculator multiplies these portions by your current weight ÷ 80 kg. Check labels; the sample’s calories and grams are estimates for that 80 kg illustration."),
    ),
    block("grocery", "Grocery list",
      el("div", { class: "stack" }, grocery.map(([name, items]) => el("article", { class: "kv" }, [
        el("h3", {}, [name]),
        el("p", {}, [items]),
      ]))),
    ),
    block("flex", "Compliance tiers",
      stack(["Tier", "Behaviors", "Why"], compliance.map((row) => [row.tier, row.behaviors, row.why])),
      p(complianceRule),
    ),
  );
  return root;
}

function resultCard(result) {
  if (!result.ok) {
    return el("div", { class: "card result warn" }, [el("p", {}, [result.message])]);
  }
  const unit = result.unit;
  const lossLow = fromKg(result.weeklyLossKg.low, unit);
  const lossHigh = fromKg(result.weeklyLossKg.high, unit);
  const unitLabel = unit === "lb" ? "lb" : "kg";
  const emphasis = result.deficitEmphasis === "high"
    ? "There is a lot of fat to lose, so put the deficit at the top of the range, about 500 kcal/day, and use the protein figures below (they are based on goal weight)."
    : result.deficitEmphasis === "low"
      ? "Already fairly lean, so use the low end: a deficit near 300 kcal/day. Protein stays 1.6–2.2 g/kg of current weight. The plan’s “low end” is the contrast with sitting at the top of the deficit range."
      : "Use the full ranges. Larger bodies can sit at the high end of the deficit.";
  const portion = result.portionEnd === "upper"
    ? "For the plate method, men and bigger or more active people usually need the upper end of each hand portion."
    : result.portionEnd === "lower"
      ? "For the plate method, women and smaller people usually need the lower end of each hand portion. Compare the same cycle phase month to month, and expect more water swings. Plan targets don’t change."
      : "Plan targets don’t change with sex. On the plate, use the upper end of each portion if you are bigger or more active, and the lower end if you are smaller.";
  const activity = result.activity === "busy"
    ? "Busy week: Template C, about 1.7–2 h, and steps at least 7,000–8,000. The calorie and protein ranges do not get a separate formula."
    : "At 4–5 h/week, planned exercise often burns ~1,500–3,000 kcal/week depending on body size and intensity (the plan’s estimate). Don’t add that on top of maintenance by hand.";
  const nodes = [
    el("h2", {}, ["Your ranges"]),
    p(emphasis),
    el("div", { class: "stats" }, [
      stat(`${fmt(result.protein.low, 0)}–${fmt(result.protein.high, 0)} g`, `Protein per day, 1.6–2.2 g/kg of ${fmt(result.basisKg, 1)} kg`),
      stat(`~${fmt(result.protein.perMeal, 0)} g`, "Per feeding, ~0.4 g/kg, across 3–5 meals"),
      stat(`${fmt(lossLow, 1)}–${fmt(lossHigh, 1)} ${unitLabel}`, "Per week, 0.5–0.7% of current weight"),
      stat("300–500 kcal", "Below maintenance each day"),
    ]),
  ];
  if (result.intake) {
    const near = result.deficitEmphasis === "high"
      ? ` Aim nearer ${fmt(result.intake.low, 0)} kcal.`
      : result.deficitEmphasis === "low"
        ? ` Aim nearer ${fmt(result.intake.high, 0)} kcal.`
        : "";
    nodes.push(p(`Intake to aim for: ${fmt(result.intake.low, 0)}–${fmt(result.intake.high, 0)} kcal/day, which is ${fmt(result.intake.maintenance, 0)} minus the 300–500 kcal deficit.${near} Predictive equations can be off by hundreds of kcal.`));
  } else {
    nodes.push(p("Once you know maintenance, subtract 300–500 kcal/day. Until then, judge the week by whether average weight is falling 0.5–0.7%."));
  }
  nodes.push(p(portion));
  nodes.push(p(activity));
  nodes.push(p(`The sample day is built for ~80 kg. Scale those portions by ${fmt(result.sampleScale, 2)}× (your current weight divided by 80).`));
  nodes.push(el("p", {}, [
    el("button", {
      type: "button",
      class: "texty",
      onclick: () => {
        prefs.template = result.activity === "busy" ? "C" : (prefs.template === "C" ? "A" : prefs.template);
        savePrefs();
        go("templates");
      },
    }, [result.activity === "busy" ? "Use Template C in Training" : "Open the training templates"]),
  ]));
  nodes.push(el("ul", { class: "list tight" }, [
    el("li", {}, ["Fiber ≥30 g/day."]),
    el("li", {}, ["Sodium about 1,500–2,300 mg/day, mostly by cutting restaurant and packaged food."]),
    el("li", {}, ["Potassium from food, 3,500–5,000 mg/day. Not pills unless a doctor approves."]),
    el("li", {}, ["Alcohol ideally ≤3–4 drinks/week, ≤2 per occasion, none within ~3 h of bed."]),
    el("li", {}, ["About 80–90% of calories from whole or minimally processed foods."]),
  ]));
  return el("div", { class: "card result" }, nodes);
}

function renderSleep() {
  return el("div", {}, [
    el("p", { class: "eyebrow" }, ["Sleep"]),
    el("h1", {}, ["Seven hours, and the same wake time"]),
    p("Plan 7.5–8.5 h in bed so you actually sleep at least 7 h. A consistent wake time, within 30–60 minutes all week, matters as much as the total."),
    block("findings", "What the studies mean here",
      stack(["Finding", "What it means for you", "Evidence"], sleepFindings),
    ),
    block("routine", "Sleep routine",
      stack(["Time", "Habit"], sleepRoutine),
    ),
    block("lifestyle", "Stress, sunlight, and the rest",
      stack(["Factor", "Practical guidance", "Evidence"], lifestyle),
    ),
  ]);
}

function renderSupplements() {
  const order = ["Strong", "Strong (if low intake)", "Moderate", "Moderate-Weak", "Weak / skip", "Use caution"];
  return el("div", {}, [
    el("p", { class: "eyebrow" }, ["Supplements"]),
    el("h1", {}, ["Creatine first. Most of the rest is optional."]),
    p("No prescription drugs. Food covers nitrate, potassium, and fish oil before any powder does. Third-party tested products (NSF Certified for Sport or Informed Choice) when you do buy one."),
    ...order.map((tier) => {
      const rows = supplements.filter((item) => item.tier === tier);
      if (!rows.length) return null;
      return block(`tier-${tier.replace(/[^a-z]+/gi, "-").toLowerCase()}`, tier,
        ...rows.map((item) => el("article", { class: "kv supplement" }, [
          el("h3", {}, [item.name]),
          el("p", { class: "dose" }, [rich(item.dose)]),
          p(item.effect),
          el("p", { class: "fine" }, [rich(item.safety)]),
          el("p", { class: "tags" }, [el("span", { class: "tag" }, [item.cost])]),
        ])),
      );
    }),
    p(supplementNote, "fine"),
  ]);
}

function renderTrack() {
  const trend = trendWindow(checkins, 3);
  const root = el("div", {}, [
    el("p", { class: "eyebrow" }, ["Tracking"]),
    el("h1", {}, ["A weekly check-in, kept in this browser"]),
    p("Log the week’s average weight, waist, a note on the main lifts, steps, and sleep. Nothing is uploaded. The plan wants a 7-day average of morning weights, and it says not to judge a stall before 2–3 weeks."),
    jumps([["checkin", "Check-in"], ["trend", "Trend"], ["adjust", "If it stalls"], ["labs", "Labs"]]),
  ]);
  if (banner) {
    root.append(el("p", { class: "banner", role: "status" }, [banner]));
  }
  root.append(checkinForm(), trendBlock(trend), logList(), expectations());
  return root;
}

function checkinForm() {
  const weightUnit = prefs.unit === "lb" ? "lb" : "kg";
  const waistUnit = prefs.waistUnit === "in" ? "in" : "cm";
  const form = el("form", { class: "card", id: "checkin" }, [
    el("h2", {}, ["This week"]),
    field("Week ending", el("input", { type: "date", name: "date", required: true, value: todayISO() })),
    choiceGroup("wunit", "Weight unit", [["kg", "kg"], ["lb", "lb"]], prefs.unit, (value) => {
      prefs.unit = value;
      savePrefs();
      const input = form.querySelector("[name='weight']");
      const label = input && input.parentElement.querySelector(".field-l");
      if (label) label.textContent = `Weight, 7-day average (${value === "lb" ? "lb" : "kg"})`;
      if (input) input.placeholder = value === "lb" ? "176.4" : "80.0";
    }),
    field(`Weight, 7-day average (${weightUnit})`, el("input", {
      name: "weight",
      inputmode: "decimal",
      required: true,
      placeholder: weightUnit === "lb" ? "176.4" : "80.0",
    })),
    choiceGroup("waistunit", "Waist unit", [["cm", "cm"], ["in", "in"]], waistUnit, (value) => {
      prefs.waistUnit = value;
      savePrefs();
      const input = form.querySelector("[name='waist']");
      const label = input && input.parentElement.querySelector(".field-l");
      if (label) label.textContent = `Waist at the navel, relaxed (${value === "in" ? "in" : "cm"})`;
      if (input) input.placeholder = value === "in" ? "34" : "86";
    }),
    field(`Waist at the navel, relaxed (${waistUnit})`, el("input", {
      name: "waist",
      inputmode: "decimal",
      placeholder: waistUnit === "in" ? "34" : "86",
    }), "Optional. After a normal exhale."),
    field("Steps, daily average", el("input", { name: "steps", inputmode: "numeric", placeholder: "8500" })),
    field("Sleep, typical hours", el("input", { name: "sleep", inputmode: "decimal", placeholder: "7.5" })),
    field("Squat (load × reps × RPE)", el("input", { name: "squat", placeholder: "100 kg × 6 @ RPE 8" })),
    field("Press (load × reps × RPE)", el("input", { name: "press", placeholder: "60 kg × 8 @ RPE 8" })),
    field("Hinge (load × reps × RPE)", el("input", { name: "hinge", placeholder: "140 kg × 5 @ RPE 7" })),
    field("Note", el("textarea", { name: "note", rows: "2", maxlength: "200" })),
    el("p", { class: "fine" }, ["Saving the same date replaces that week."]),
    el("button", { type: "submit", class: "button" }, ["Save check-in"]),
  ]);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    const date = String(data.get("date") || "");
    const weightRaw = Number(data.get("weight"));
    const weightKg = toKg(weightRaw, prefs.unit);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || weightKg == null || weightKg < 30 || weightKg > 300) {
      showFormError(form, "Enter a date and a body weight between 30 and 300 kg (about 66–660 lb).");
      return;
    }
    let waistCm = null;
    const waistRaw = String(data.get("waist") || "").trim();
    if (waistRaw !== "") {
      const waist = Number(waistRaw);
      waistCm = prefs.waistUnit === "in" ? waist * CM_PER_IN : waist;
      if (!Number.isFinite(waist) || waistCm < 40 || waistCm > 200) {
        showFormError(form, "Waist looks off. Use centimeters, or inches if that unit is selected.");
        return;
      }
    }
    const stepsRaw = String(data.get("steps") || "").trim();
    const sleepRaw = String(data.get("sleep") || "").trim();
    const steps = stepsRaw === "" ? null : Number(stepsRaw);
    const sleep = sleepRaw === "" ? null : Number(sleepRaw);
    if (steps != null && (!Number.isFinite(steps) || steps < 0 || steps > 100000)) {
      showFormError(form, "Steps should be a daily average between 0 and 100,000.");
      return;
    }
    if (sleep != null && (!Number.isFinite(sleep) || sleep < 0 || sleep > 14)) {
      showFormError(form, "Sleep should be hours between 0 and 14.");
      return;
    }
    const text = (key) => String(data.get(key) || "").trim().slice(0, 200);
    const row = {
      date,
      weight: weightKg,
      waist: waistCm,
      steps,
      sleep,
      squat: text("squat"),
      press: text("press"),
      hinge: text("hinge"),
      note: text("note"),
    };
    checkins = checkins.filter((item) => item.date !== date).concat(row);
    saveLog();
    banner = `Saved the week ending ${formatDate(date)}.`;
    render();
    document.getElementById("trend")?.scrollIntoView({ block: "start" });
  });
  return form;
}

function trendBlock(trend) {
  const nodes = [el("h2", {}, ["Trend"]), p(trendCopy[trend.kind] || trendCopy.mixed)];
  if (trend.kind !== "need-data" && trend.kind !== "need-span") {
    const loss = fromKg(Math.abs(trend.deltaKg), prefs.unit);
    const unit = prefs.unit === "lb" ? "lb" : "kg";
    const direction = trend.deltaKg < 0 ? "down" : trend.deltaKg > 0 ? "up" : "unchanged";
    nodes.push(p(
      `From ${formatDate(trend.from)} to ${formatDate(trend.to)} (${trend.points.length} check-ins, ${fmt(trend.weeks, 1)} weeks): weight ${direction} ${fmt(loss, 1)} ${unit}, ${fmt(Math.abs(trend.pctPerWeek), 2)}% of the starting weight per week.`,
    ));
    if (trend.waistDeltaCm == null) {
      nodes.push(p("Waist wasn’t on both ends of this window, so the recomp check can’t run.", "fine"));
    } else {
      const waistUnit = prefs.waistUnit === "in" ? "in" : "cm";
      const waistDelta = prefs.waistUnit === "in" ? trend.waistDeltaCm / CM_PER_IN : trend.waistDeltaCm;
      nodes.push(p(`Waist change over the same check-ins: ${waistDelta > 0 ? "+" : ""}${fmt(waistDelta, 1)} ${waistUnit}.`, "fine"));
    }
    nodes.push(p(flatDisclosure, "fine"));
    const extras = [];
    if (trend.stepsAvg != null) {
      extras.push(trend.stepsAvg >= 8000
        ? `Steps averaged ${fmt(trend.stepsAvg, 0)}/day, inside or above the plan’s 8,000–10,000.`
        : `Steps averaged ${fmt(trend.stepsAvg, 0)}/day, under the plan’s 8,000–10,000. Busy weeks still want at least 7,000–8,000.`);
    }
    if (trend.sleepAvg != null) {
      extras.push(trend.sleepAvg >= 7
        ? `Sleep averaged ${fmt(trend.sleepAvg, 1)} h, which meets the ≥7 h target.`
        : `Sleep averaged ${fmt(trend.sleepAvg, 1)} h, under the ≥7 h target.`);
    }
    if (extras.length) nodes.push(el("ul", { class: "list tight" }, extras.map((line) => el("li", {}, [line]))));
    const weightPoints = trend.allPoints.map((row) => ({ date: row.date, y: row.weight }));
    nodes.push(chartCard("Weight", weightPoints, prefs.unit === "lb" ? "lb" : "kg", true));
    const waistUnit = prefs.waistUnit === "in" ? "in" : "cm";
    const waistPoints = trend.allPoints
      .filter((row) => row.waist > 0)
      .map((row) => ({ date: row.date, y: waistUnit === "in" ? row.waist / CM_PER_IN : row.waist }));
    if (waistPoints.length >= 2) nodes.push(chartCard("Waist", waistPoints, waistUnit, false));
  }
  const tools = el("div", { class: "actions" }, [
    el("button", { type: "button", class: "button secondary", onclick: exportLog }, ["Export JSON"]),
    el("label", { class: "button secondary file" }, [
      "Import JSON",
      el("input", { type: "file", accept: "application/json", onchange: importLog }),
    ]),
    checkins.length
      ? el("button", { type: "button", class: "button ghost", onclick: clearLog }, ["Clear log"])
      : null,
  ]);
  nodes.push(tools);
  return el("section", { class: "block", id: "trend" }, nodes);
}

function chartCard(title, points, unit, guides) {
  const ys = points.map((point) => (title === "Weight" && unit === "lb" ? fromKg(point.y, "lb") : point.y));
  const display = points.map((point, index) => ({ date: point.date, y: ys[index] }));
  let guideLines = [];
  if (guides && display.length >= 2) {
    const start = display[0].y;
    guideLines = [
      { y: start * 0.95, label: "−5%" },
      { y: start * 0.90, label: "−10%" },
    ];
  }
  const svg = lineChart(display, guideLines);
  const first = display[0];
  const last = display[display.length - 1];
  svg.setAttribute("aria-label", `${title} from ${fmt(first.y, 1)} to ${fmt(last.y, 1)} ${unit} across ${display.length} check-ins.`);
  return el("figure", { class: "chart-card" }, [
    el("figcaption", {}, [`${title} (${unit})`]),
    svg,
    guides ? el("p", { class: "fine" }, ["Dashed lines are 5% and 10% below the first logged weight, the plan’s loss goal."]) : null,
  ]);
}

function lineChart(points, guides) {
  const width = 640;
  const height = 200;
  const padL = 44;
  const padR = 12;
  const padT = 16;
  const padB = 28;
  const ys = points.map((point) => point.y).concat(guides.map((guide) => guide.y));
  let min = Math.min(...ys);
  let max = Math.max(...ys);
  if (min === max) {
    min -= 1;
    max += 1;
  }
  const pad = (max - min) * 0.12;
  min -= pad;
  max += pad;
  const xAt = (index) => padL + (points.length === 1 ? (width - padL - padR) / 2 : (index / (points.length - 1)) * (width - padL - padR));
  const yAt = (value) => padT + ((max - value) / (max - min)) * (height - padT - padB);
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("class", "chart");
  svg.setAttribute("role", "img");
  const title = document.createElementNS("http://www.w3.org/2000/svg", "title");
  title.textContent = "Check-in trend";
  svg.append(title);
  const axis = (x1, y1, x2, y2, className) => {
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", x1);
    line.setAttribute("y1", y1);
    line.setAttribute("x2", x2);
    line.setAttribute("y2", y2);
    line.setAttribute("class", className);
    return line;
  };
  svg.append(axis(padL, padT, padL, height - padB, "axis"), axis(padL, height - padB, width - padR, height - padB, "axis"));
  guides.forEach((guide) => {
    const y = yAt(guide.y);
    svg.append(axis(padL, y, width - padR, y, "guide"));
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", width - padR);
    label.setAttribute("y", y - 4);
    label.setAttribute("text-anchor", "end");
    label.setAttribute("class", "guide-label");
    label.textContent = guide.label;
    svg.append(label);
  });
  const poly = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  poly.setAttribute("class", "series");
  poly.setAttribute("points", points.map((point, index) => `${xAt(index)},${yAt(point.y)}`).join(" "));
  svg.append(poly);
  points.forEach((point, index) => {
    const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    dot.setAttribute("class", "dot");
    dot.setAttribute("cx", xAt(index));
    dot.setAttribute("cy", yAt(point.y));
    dot.setAttribute("r", "3.5");
    svg.append(dot);
  });
  const labelFor = (text, x, anchor) => {
    const node = document.createElementNS("http://www.w3.org/2000/svg", "text");
    node.setAttribute("x", x);
    node.setAttribute("y", height - 8);
    node.setAttribute("text-anchor", anchor);
    node.setAttribute("class", "axis-label");
    node.textContent = text;
    return node;
  };
  svg.append(labelFor(points[0].date.slice(5), xAt(0), "start"));
  if (points.length > 1) svg.append(labelFor(points[points.length - 1].date.slice(5), xAt(points.length - 1), "end"));
  return svg;
}

function logList() {
  if (!checkins.length) {
    return el("section", { class: "block", id: "log" }, [
      el("h2", {}, ["Log"]),
      p("No weeks saved yet. A useful first entry is this morning’s 7-day average, even if the earlier days are a guess you replace later."),
    ]);
  }
  const rows = [...checkins].sort((a, b) => (a.date < b.date ? 1 : -1));
  return el("section", { class: "block", id: "log" }, [
    el("h2", {}, ["Log"]),
    el("div", { class: "stack" }, rows.map((row) => {
      const weight = fromKg(row.weight, prefs.unit);
      const unit = prefs.unit === "lb" ? "lb" : "kg";
      const bits = [`${fmt(weight, 1)} ${unit}`];
      if (row.waist) {
        const waist = prefs.waistUnit === "in" ? row.waist / CM_PER_IN : row.waist;
        bits.push(`waist ${fmt(waist, 1)} ${prefs.waistUnit === "in" ? "in" : "cm"}`);
      }
      if (row.steps != null) bits.push(`${Math.round(row.steps)} steps`);
      if (row.sleep != null) bits.push(`${fmt(row.sleep, 1)} h sleep`);
      const lifts = [row.squat, row.press, row.hinge].filter(Boolean);
      return el("article", { class: "kv" }, [
        el("div", { class: "log-head" }, [
          el("h3", {}, [formatDate(row.date)]),
          el("button", {
            type: "button",
            class: "texty",
            onclick: () => {
              checkins = checkins.filter((item) => item.date !== row.date);
              saveLog();
              banner = `Removed ${formatDate(row.date)}.`;
              render();
            },
          }, ["Remove"]),
        ]),
        el("p", {}, [bits.join(" · ")]),
        lifts.length ? el("p", { class: "fine" }, [lifts.join(" · ")]) : null,
        row.note ? el("p", { class: "fine" }, [row.note]) : null,
      ]);
    })),
  ]);
}

function expectations() {
  return el("div", {}, [
    block("good", "What “good” looks like",
      stack(["Metric", "How", "Frequency", "Good"], trackingMetrics),
    ),
    block("outcomes", "Realistic outcomes",
      stack(["Outcome", "12 weeks", "24 weeks", "Basis"], outcomes),
    ),
    block("adjust", "When progress stalls",
      p("Check after at least 2–3 weeks. Change one thing at a time."),
      stack(["Situation", "First check", "Then adjust"], adjustments),
      p(adjustmentNote, "fine"),
    ),
    block("labs", "Labs at baseline and week 12",
      stack(["Test", "Why", "Reference context"], labs),
      p(labsNote),
    ),
  ]);
}

function showFormError(form, message) {
  let note = form.querySelector(".form-error");
  if (!note) {
    note = el("p", { class: "banner form-error", role: "status" });
    form.prepend(note);
  }
  note.textContent = message;
}

function exportLog() {
  const payload = {
    version: 1,
    weightUnit: "kg",
    waistUnit: "cm",
    checkins,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = el("a", { href: url, download: "woooosh-recomp-checkins.json" });
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function importLog(event) {
  const file = event.target.files && event.target.files[0];
  event.target.value = "";
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const data = JSON.parse(String(reader.result));
      const rows = Array.isArray(data) ? data : data.checkins;
      if (!Array.isArray(rows)) throw new Error("missing checkins");
      const next = [];
      rows.forEach((row) => {
        if (!row || !/^\d{4}-\d{2}-\d{2}$/.test(row.date)) return;
        const weight = Number(row.weight);
        if (!Number.isFinite(weight) || weight <= 0) return;
        const text = (value) => (typeof value === "string" ? value.slice(0, 200) : "");
        const num = (value) => {
          if (value == null || value === "") return null;
          const n = Number(value);
          return Number.isFinite(n) ? n : null;
        };
        next.push({
          date: row.date,
          weight,
          waist: num(row.waist),
          steps: num(row.steps),
          sleep: num(row.sleep),
          squat: text(row.squat),
          press: text(row.press),
          hinge: text(row.hinge),
          note: text(row.note),
        });
      });
      if (!next.length) {
        banner = "That file has no usable check-ins. Weight is stored in kilograms.";
        render();
        return;
      }
      checkins = next;
      saveLog();
      banner = `Imported ${next.length} check-in${next.length === 1 ? "" : "s"}. Weight in the file is kilograms.`;
      render();
    } catch {
      banner = "Couldn’t read that file. Export a backup from this page and use that shape.";
      render();
    }
  };
  reader.readAsText(file);
}

function clearLog() {
  if (!confirm("Delete every check-in saved in this browser?")) return;
  checkins = [];
  saveLog();
  banner = "Check-ins cleared.";
  render();
}

const views = {
  plan: renderPlan,
  train: renderTrain,
  eat: renderEat,
  sleep: renderSleep,
  supplements: renderSupplements,
  track: renderTrack,
  references: renderReferences,
};

function renderReferences() {
  return el("div", {}, [
    el("p", { class: "eyebrow" }, ["References"]),
    el("h1", {}, ["61 sources, checked October 2026"]),
    p(grades),
    el("ol", { class: "refs" }, referencesList()),
  ]);
}

function referencesList() {
  return referencesFromData().map((ref) => el("li", { id: `ref-${ref.n}` }, [
    el("span", {}, [ref.citation + " "]),
    el("a", { href: ref.url, target: "_blank", rel: "noopener noreferrer" }, [ref.url.replace(/^https:\/\//, "")]),
    ref.also ? el("span", {}, [
      " ",
      ref.also.label,
      " ",
      el("a", { href: ref.also.url, target: "_blank", rel: "noopener noreferrer" }, [ref.also.url.replace(/^https:\/\//, "")]),
    ]) : null,
  ]));
}

function referencesFromData() {
  return references;
}

function render() {
  const { section, anchor } = parseHash();
  const keep = preserveScroll;
  const y = window.scrollY;
  preserveScroll = false;
  applyTheme();
  renderNav(section);
  document.title = `${nav.find((item) => item.id === section).label} · woooosh`;
  main.replaceChildren(views[section]());
  if (keep) {
    window.scrollTo(0, y);
    return;
  }
  if (anchor) {
    const scroll = () => document.getElementById(anchor)?.scrollIntoView({ block: "start" });
    scroll();
    requestAnimationFrame(scroll);
  } else {
    window.scrollTo(0, 0);
  }
}

function rerender() {
  preserveScroll = true;
  render();
}

themeBtn.addEventListener("click", () => {
  const dark = themeBtn.getAttribute("aria-pressed") === "true";
  prefs.theme = dark ? "light" : "dark";
  savePrefs();
  applyTheme();
});

window.addEventListener("hashchange", () => {
  banner = "";
  render();
});

if (!location.hash) history.replaceState(null, "", "#plan");
render();
