import { LIFTS, programById } from './programs.js';

export function roundToLoadable(w, settings) {
  const res = 2 * Math.min(...settings.plates);
  const rounded = Math.round(w / res) * res;
  return Math.max(rounded, settings.barWeight);
}

export function platesPerSide(weight, settings) {
  let rem = (weight - settings.barWeight) / 2;
  if (rem < 0) return null;
  const out = [];
  for (const p of [...settings.plates].sort((a, b) => b - a)) {
    let n = 0;
    while (rem >= p - 1e-9) { rem -= p; n++; }
    if (n) out.push({ plate: p, count: n });
  }
  return rem > 1e-9 ? null : out;
}

export function warmupSets(lift, work, settings) {
  if (LIFTS[lift].bodyweight) return [];
  const bar = settings.barWeight;
  const sets = [];
  // Deadlifts and cleans start from the floor with plates on — no empty-bar sets
  if (lift !== 'deadlift') sets.push({ weight: bar, reps: 5, times: 2 });
  const floor = lift === 'deadlift' ? Math.min(work, roundToLoadable(bar + 2 * Math.min(...settings.plates) * 4, settings)) : bar;
  const steps = [
    { pct: 0.45, reps: 5 },
    { pct: 0.65, reps: 3 },
    { pct: 0.85, reps: 2 },
  ];
  for (const s of steps) {
    const w = roundToLoadable(floor + (work - floor) * s.pct, settings);
    if (w > bar && w < work && (sets.length === 0 || w > sets[sets.length - 1].weight)) {
      sets.push({ weight: w, reps: s.reps });
    }
  }
  return sets;
}

function altIndex(state, program, slot) {
  const counters = state.program.alt || {};
  return ((counters[slot.key] || 0) + (slot.altOffset || 0)) % slot.options.length;
}

// Resolve the current day's template into concrete exercises with weights.
export function resolveWorkout(state) {
  const program = programById(state.program.id);
  const dayIdx = state.program.dayIndex % program.days.length;
  const day = program.days[dayIdx];
  const exercises = day.slots.map((slot) => {
    let lift, sets, reps, amrap = false, pct = null, progresses = false, tag = slot.tag || null;
    if (slot.slot === 'alt') {
      const opt = slot.options[altIndex(state, program, slot)];
      lift = opt.lift; sets = opt.sets; reps = opt.reps;
      pct = slot.pct || null;
      progresses = !pct;
    } else {
      lift = slot.lift; sets = slot.sets; reps = slot.reps;
      amrap = !!slot.amrap;
      pct = slot.slot === 'pct' ? slot.pct : null;
      progresses = slot.slot === 'main' && !slot.fixed && !LIFTS[lift].bodyweight;
    }
    const rec = state.lifts[pct ? (slot.of || lift) : lift];
    let weight = 0;
    if (!LIFTS[lift].bodyweight && rec) {
      weight = pct ? roundToLoadable(rec.weight * pct, state.settings) : rec.weight;
    }
    return { lift, name: LIFTS[lift].name, sets, reps: amrap ? null : reps, amrap, weight, tag, progresses };
  });
  return { program, day, dayIdx, label: dayLabel(program, day, exercises), exercises };
}

function dayLabel(program, day, exercises) {
  if (program.days.length > 1 && day.label !== 'Workout') return day.label;
  const press = exercises.find((e) => e.lift === 'press' || e.lift === 'bench');
  return press ? (press.lift === 'press' ? 'Workout A' : 'Workout B') : day.label;
}

// Apply results of a finished session: progression, stall counting, alternation
// counters, day index. Mutates a copy of state and returns it with a summary.
export function completeWorkout(state, logged) {
  const program = programById(state.program.id);
  const day = program.days[state.program.dayIndex % program.days.length];
  const next = structuredClone(state);
  const summary = [];

  for (const ex of logged.exercises) {
    if (!ex.progresses || LIFTS[ex.lift].bodyweight) continue;
    const rec = next.lifts[ex.lift];
    if (!rec) continue;
    const done = ex.setsDone.filter((r) => r != null);
    const success = done.length === ex.sets && done.every((r) => r >= ex.reps);
    if (success) {
      rec.weight = roundToLoadable(rec.weight + rec.increment, next.settings);
      rec.fails = 0;
      summary.push({ lift: ex.lift, kind: 'up', to: rec.weight });
    } else if (done.length > 0) {
      rec.fails = (rec.fails || 0) + 1;
      if (rec.fails >= 3) {
        rec.weight = roundToLoadable(rec.weight * 0.9, next.settings);
        rec.fails = 0;
        summary.push({ lift: ex.lift, kind: 'deload', to: rec.weight });
      } else {
        summary.push({ lift: ex.lift, kind: 'hold', to: rec.weight, fails: rec.fails });
      }
    }
  }

  next.program.alt = next.program.alt || {};
  const advance = program.altAdvance || {};
  const lastDay = state.program.dayIndex % program.days.length === program.days.length - 1;
  for (const slot of day.slots) {
    if (slot.slot !== 'alt') continue;
    const mode = advance[slot.key] || 'per-appearance';
    if (mode === 'per-appearance' && !slot.altOffset) {
      next.program.alt[slot.key] = (next.program.alt[slot.key] || 0) + 1;
    }
  }
  if (lastDay) {
    for (const [key, mode] of Object.entries(advance)) {
      if (mode === 'cycle-end') next.program.alt[key] = (next.program.alt[key] || 0) + 1;
    }
  }
  next.program.dayIndex = state.program.dayIndex + 1;
  return { next, summary };
}

export function epley1RM(weight, reps) {
  if (!weight || !reps) return 0;
  return reps === 1 ? weight : weight * (1 + reps / 30);
}

// Best work-set weight per session for a lift, for charting.
export function liftHistory(state, lift) {
  const pts = [];
  for (const s of state.history) {
    let best = null;
    for (const ex of s.exercises) {
      if (ex.lift !== lift || !ex.weight) continue;
      const done = ex.setsDone.filter((r) => r != null && r > 0);
      if (!done.length) continue;
      const topReps = Math.max(...done);
      if (!best || ex.weight > best.weight) best = { weight: ex.weight, reps: topReps };
    }
    if (best) pts.push({ date: s.date, weight: best.weight, e1rm: epley1RM(best.weight, Math.min(best.reps, 10)) });
  }
  return pts;
}

export function sessionTonnage(session) {
  let t = 0;
  for (const ex of session.exercises) {
    if (!ex.weight) continue;
    for (const r of ex.setsDone) if (r) t += ex.weight * r;
  }
  return t;
}
