// Program definitions from Starting Strength (Rippetoe), Practical Programming,
// and Wendler’s 5/3/1 and Big Boy templates.
// Slot kinds:
//   main — fixed lift at its current work weight, drives linear progression
//   alt  — rotates through options on an alternation counter (press/bench, DL/clean)
//   pct  — derived percentage of another lift's work weight, never progresses

export const LIFTS = {
  squat:      { name: 'Squat',          short: 'SQ', slot: 1 },
  bench:      { name: 'Bench Press',    short: 'BP', slot: 2 },
  deadlift:   { name: 'Deadlift',       short: 'DL', slot: 3 },
  press:      { name: 'Press',          short: 'PR', slot: 4 },
  powerclean: { name: 'Power Clean',    short: 'PC', slot: 5 },
  chinup:     { name: 'Chin-Up',        short: 'CH', slot: 6, bodyweight: true },
  backext:    { name: 'Back Extension', short: 'BE', slot: 7, bodyweight: true },
  row:        { name: 'Barbell Row',    short: 'RW', slot: 8 },
};

export const DEFAULTS = {
  lb: {
    start:     { squat: 95, bench: 65, press: 45, deadlift: 135, powerclean: 65, row: 95 },
    increment: { squat: 5, bench: 5, press: 2.5, deadlift: 10, powerclean: 5, row: 5 },
    bar: 45,
    plates: [45, 35, 25, 10, 5, 2.5, 1.25],
  },
  kg: {
    start:     { squat: 40, bench: 30, press: 20, deadlift: 60, powerclean: 30, row: 40 },
    increment: { squat: 2.5, bench: 2.5, press: 1, deadlift: 5, powerclean: 2.5, row: 2.5 },
    bar: 20,
    plates: [20, 15, 10, 5, 2.5, 1.25, 0.5],
  },
};

const S3x5 = { slot: 'main', lift: 'squat', sets: 3, reps: 5 };
const PRESS_ALT = { slot: 'alt', key: 'press', options: [
  { lift: 'press', sets: 3, reps: 5 },
  { lift: 'bench', sets: 3, reps: 5 },
]};
const PRESS_ALT_5x5 = { slot: 'alt', key: 'press', options: [
  { lift: 'press', sets: 5, reps: 5 },
  { lift: 'bench', sets: 5, reps: 5 },
]};
const PULL_ALT = { slot: 'alt', key: 'pull', options: [
  { lift: 'deadlift', sets: 1, reps: 5 },
  { lift: 'powerclean', sets: 5, reps: 3 },
]};
// Deadlift alternates with rows in BBB; same slot key so they share the counter.
const DL_ROW_ALT = { slot: 'alt', key: 'pull', options: [
  { lift: 'deadlift', sets: 5, reps: 5 },
  { lift: 'row', sets: 3, reps: 8 },
]};
const CHINS = { slot: 'main', lift: 'chinup', sets: 3, amrap: true };
const BACKEXT = { slot: 'main', lift: 'backext', sets: 3, reps: 10, fixed: true };

// 5/3/1 percentages are of the training max (the lift's stored weight);
// each work set is its own single-set pct slot so it gets its own weight.
const WAVES_531 = [
  { week: '3×5',    sets: [[0.65, 5], [0.75, 5], [0.85, 5, true]] },
  { week: '3×3',    sets: [[0.70, 3], [0.80, 3], [0.90, 3, true]] },
  { week: '5/3/1',  sets: [[0.75, 5], [0.85, 3], [0.95, 1, true]] },
  { week: 'Deload', sets: [[0.40, 5], [0.50, 5], [0.60, 5]] },
];

function days531() {
  const order = [['press', CHINS], ['deadlift', BACKEXT], ['bench', CHINS], ['squat', BACKEXT]];
  const days = [];
  for (const { week, sets } of WAVES_531) {
    for (const [lift, assist] of order) {
      const slots = sets.map(([pct, reps, amrap]) => ({
        slot: 'pct', lift, of: lift, pct, sets: 1, reps, amrap,
        tag: amrap ? `${Math.round(pct * 100)}% · ${reps}+` : `${Math.round(pct * 100)}%`,
      }));
      if (week !== 'Deload') slots.push({ slot: 'pct', lift, of: lift, pct: 0.5, sets: 5, reps: 10, tag: 'BBB 50%' });
      days.push({ label: `${LIFTS[lift].name} · ${week}`, slots: [...slots, assist] });
    }
  }
  return days;
}

export const PROGRAMS = [
  {
    id: 'novice-1',
    name: 'Novice LP · Phase 1',
    level: 'Novice',
    schedule: '3 days / week, alternating',
    blurb: 'The original program. Squat and deadlift every workout, press and bench alternating. Add weight every single session.',
    detail: 'Phase 1 is the first two to three weeks of the Novice Linear Progression. Three exercises per workout, three workouts per week on non-consecutive days. The squat is trained every session, the press and bench press alternate, and the deadlift is pulled every workout while it is still recovering fast. Move to Phase 2 when deadlifting three times a week becomes too taxing — usually when the deadlift is well ahead of the squat.',
    progression: 'Add weight every workout: squat +5 lb, deadlift +10 lb (drop to +5 when jumps stall), press +2.5 lb, bench +5 lb. After 3 failed sessions at a weight, deload 10% and work back up.',
    days: [
      { label: 'Workout', slots: [S3x5, PRESS_ALT, { slot: 'main', lift: 'deadlift', sets: 1, reps: 5 }] },
    ],
  },
  {
    id: 'novice-2',
    name: 'Novice LP · Phase 2',
    level: 'Novice',
    schedule: '3 days / week, alternating',
    blurb: 'The power clean enters, alternating with the deadlift so the pull keeps moving without burning you out.',
    detail: 'Phase 2 introduces the power clean, alternating workout-to-workout with the deadlift. Deadlifting every session stops being sustainable once the weight gets heavy; the clean trains explosive pulling while the deadlift recovers. Everything else continues exactly as Phase 1: squat every workout, press and bench alternating, weight added every session.',
    progression: 'Same as Phase 1. Power clean moves in +5 lb jumps, then +2.5 lb as it slows. Deadlift now progresses per-appearance (roughly every other workout).',
    days: [
      { label: 'Workout', slots: [S3x5, PRESS_ALT, PULL_ALT] },
    ],
  },
  {
    id: 'novice-3',
    name: 'Novice LP · Phase 3',
    level: 'Novice',
    schedule: '3 days / week, A/B alternating',
    blurb: 'Chin-ups join the program. The full novice progression: squat, press, bench, deadlift, clean, chins.',
    detail: 'Phase 3 is the complete novice program. Workout A keeps the heavy pull (deadlift alternating with power clean); Workout B replaces it with chin-ups, done for three sets to failure. This is the phase most trainees stay in for months — ride it as long as adding weight every session still works.',
    progression: 'Barbell lifts as before. Chin-ups: add reps each session; once you get 3×10, add weight if possible. Deload a lift 10% after 3 consecutive failed sessions.',
    days: [
      { label: 'Workout A', slots: [S3x5, PRESS_ALT, PULL_ALT] },
      { label: 'Workout B', slots: [S3x5, PRESS_ALT, CHINS] },
    ],
  },
  {
    id: 'advanced-novice',
    name: 'Advanced Novice',
    level: 'Novice',
    schedule: 'Mon / Wed / Fri weekly',
    blurb: 'The last stop before intermediate: a light squat day mid-week keeps the linear progression alive a few more weeks.',
    detail: 'When Monday’s squats start ruining Wednesday’s, the Wednesday squat drops to 80% for 2 sets of 5 — light enough to recover, heavy enough to keep practicing. Pulling assistance spreads across the week: chin-ups Monday, back extensions Wednesday, and the heavy pull (deadlift alternating with power clean) on Friday. Squeeze the last weeks out of the novice progression here before moving to the Texas Method.',
    progression: 'Monday and Friday squats progress +5 lb per session; Wednesday stays at 80% of the current work weight automatically. Presses and pulls progress as in Phase 3.',
    days: [
      { label: 'Monday', slots: [S3x5, PRESS_ALT, CHINS] },
      { label: 'Wednesday', slots: [
        { slot: 'pct', lift: 'squat', of: 'squat', pct: 0.8, sets: 2, reps: 5, tag: 'Light 80%' },
        PRESS_ALT, BACKEXT,
      ]},
      { label: 'Friday', slots: [S3x5, PRESS_ALT, PULL_ALT] },
    ],
  },
  {
    id: 'texas',
    name: 'Texas Method',
    level: 'Intermediate',
    schedule: 'Mon / Wed / Fri weekly',
    blurb: 'Volume Monday, recovery Wednesday, a new 5RM every Friday. The classic intermediate program from Practical Programming.',
    detail: 'Progress now happens weekly, not per-workout. Monday is the stress: 5 sets of 5 at 90% of Friday’s five-rep max. Wednesday is active recovery: light squats at 80% of Monday, the other press at moderate weight, chin-ups. Friday is the payoff: a single all-out set of five at a new personal record. The press and bench swap weekly — whichever you push Monday and Friday, the other fills Wednesday.',
    progression: 'Friday’s 5RM goes up 5 lb per week (2.5 lb for the press); Monday’s volume and Wednesday’s light work are computed from it automatically. When Friday stalls, reset volume 10% and rebuild.',
    days: [
      { label: 'Volume', slots: [
        { slot: 'pct', lift: 'squat', of: 'squat', pct: 0.9, sets: 5, reps: 5, tag: 'Volume 90%' },
        { slot: 'alt', key: 'press', pct: 0.9, tag: 'Volume 90%', options: PRESS_ALT_5x5.options },
        BACKEXT,
      ]},
      { label: 'Recovery', slots: [
        { slot: 'pct', lift: 'squat', of: 'squat', pct: 0.72, sets: 2, reps: 5, tag: 'Light 80% of volume' },
        { slot: 'alt', key: 'press', altOffset: 1, pct: 0.72, tag: 'Light', options: PRESS_ALT.options },
        CHINS,
      ]},
      { label: 'Intensity', slots: [
        { slot: 'main', lift: 'squat', sets: 1, reps: 5, tag: 'New 5RM' },
        { slot: 'alt', key: 'press', tag: 'New 5RM', options: [
          { lift: 'press', sets: 1, reps: 5 },
          { lift: 'bench', sets: 1, reps: 5 },
        ]},
        PULL_ALT,
      ]},
    ],
    // Volume + Intensity press must match; the shared counter advances once per
    // completed workout containing the key, so it flips Volume→Recovery→Intensity.
    // Advance press alternation weekly instead: only bump after the Intensity day.
    altAdvance: { press: 'cycle-end', pull: 'per-appearance' },
  },
  {
    id: 'hlm',
    name: 'Heavy · Light · Medium',
    level: 'Intermediate',
    schedule: 'Mon / Wed / Fri weekly',
    blurb: 'The oldest template in barbell training — Bill Starr’s weekly wave, as presented in Practical Programming.',
    detail: 'One heavy dose of stress on Monday, then two progressively easier sessions that keep you moving while you recover: Wednesday at 80%, Friday at 90%. Weekly progression on the Monday sets across all lifts. HLM is more forgiving than the Texas Method and scales from late-novice through years of training by adjusting the size of the weekly jump.',
    progression: 'Monday’s 3×5 adds 5 lb per week (2.5 lb press). Light and medium days are computed at 80% and 90% of Monday. Stall three Mondays running, deload 10%.',
    days: [
      { label: 'Heavy', slots: [S3x5, PRESS_ALT, { slot: 'main', lift: 'deadlift', sets: 1, reps: 5 }] },
      { label: 'Light', slots: [
        { slot: 'pct', lift: 'squat', of: 'squat', pct: 0.8, sets: 2, reps: 5, tag: 'Light 80%' },
        { slot: 'alt', key: 'press', altOffset: 1, tag: 'Other press', options: PRESS_ALT.options },
        CHINS,
      ]},
      { label: 'Medium', slots: [
        { slot: 'pct', lift: 'squat', of: 'squat', pct: 0.9, sets: 2, reps: 5, tag: 'Medium 90%' },
        { slot: 'alt', key: 'press', pct: 0.9, tag: '90%', options: PRESS_ALT.options },
        { slot: 'main', lift: 'powerclean', sets: 5, reps: 3 },
      ]},
    ],
    altAdvance: { press: 'cycle-end' },
  },
  {
    id: 'split',
    name: 'Four-Day Split',
    level: 'Advanced',
    schedule: 'Mon / Tue / Thu / Fri weekly',
    blurb: 'For the advanced trainee: pressing and pulling split across four shorter, more focused sessions.',
    detail: 'Advanced programming in Practical Programming is individual by definition — by this stage you know your own recovery. The four-day split is the standard template it builds from: squat and press volume early in the week, intensity later, with the deadlift anchoring its own day. Sessions are shorter and each lift gets full attention. Adjust percentages and jumps to your own rate of adaptation.',
    progression: 'Weekly progression on the primary sets, like the Texas Method. Treat the template as a starting point — advanced trainees are expected to tune volume and intensity to their own response.',
    days: [
      { label: 'Press · Volume', slots: [
        { slot: 'pct', lift: 'press', of: 'press', pct: 0.9, sets: 5, reps: 5, tag: 'Volume 90%' },
        { slot: 'pct', lift: 'bench', of: 'bench', pct: 0.72, sets: 3, reps: 5, tag: 'Light' },
        CHINS,
      ]},
      { label: 'Squat · Volume', slots: [
        { slot: 'pct', lift: 'squat', of: 'squat', pct: 0.9, sets: 5, reps: 5, tag: 'Volume 90%' },
        BACKEXT,
      ]},
      { label: 'Press · Intensity', slots: [
        { slot: 'main', lift: 'bench', sets: 1, reps: 5, tag: 'New 5RM' },
        { slot: 'pct', lift: 'press', of: 'press', pct: 0.72, sets: 3, reps: 5, tag: 'Light' },
        { slot: 'main', lift: 'powerclean', sets: 5, reps: 3 },
      ]},
      { label: 'Pull · Intensity', slots: [
        { slot: 'main', lift: 'squat', sets: 1, reps: 5, tag: 'New 5RM' },
        { slot: 'main', lift: 'deadlift', sets: 1, reps: 5, tag: 'New 5RM' },
      ]},
    ],
  },
  // ── 5/3/1 (Wendler) ─────────────────────────────────────────────────
  {
    id: 'five-three-one',
    name: '5/3/1 · Boring But Big',
    level: 'Intermediate',
    schedule: '4 days / week · 4-week cycle',
    blurb: 'Wendler’s 5/3/1: monthly waves of 5s, 3s, and a PR single off a training max, with Boring But Big assistance.',
    detail: 'Jim Wendler’s 5/3/1 trains each big lift once a week, working off a training max — set each lift’s weight to about 90% of your best single. Week one ramps to a top set of 5+, week two 3+, week three the 5/3/1 week with a 95% single for 1+, week four deloads. Top sets are AMRAP: beat the minimum by as many reps as you have in you. Boring But Big follows the main work — 5 sets of 10 at 50% of the training max — plus chins or back extensions.',
    progression: 'Training maxes go up by each lift’s increment once per four-week cycle, never per workout. Set increments to +5 lb for the press and bench and +10 lb for the squat and deadlift in Settings. If a top set misses its minimum reps, drop that lift’s training max 10% and rebuild.',
    days: days531(),
    cycleBump: ['press', 'deadlift', 'bench', 'squat'],
  },
  // ── Big Boy templates (Wendler) ─────────────────────────────────────
  {
    id: 'bbb',
    name: 'Big Boy',
    level: 'Intermediate',
    schedule: 'Mon / Tue / Fri weekly',
    blurb: 'Wendler’s Big Boy template: two squat days early in the week, both presses trained weekly, deadlifts alternating with rows.',
    detail: 'Jim Wendler’s Big Boy template as posted around the Starting Strength boards. Monday and Tuesday both squat — Monday with the week’s primary press, Tuesday with the heavy pull (deadlift alternating with barbell rows). Friday is a lighter session on the other press with assistance work, so both the press and bench get trained every week.',
    progression: 'Squats progress per session as in the novice LP. The presses swap Monday/Friday roles each week; the deadlift and row alternate per appearance. Deload a lift 10% after 3 consecutive failed sessions.',
    days: [
      { label: 'Squat · Press', slots: [S3x5, PRESS_ALT, BACKEXT, CHINS] },
      { label: 'Squat · Pull', slots: [S3x5, DL_ROW_ALT, CHINS] },
      { label: 'Press · Recovery', slots: [
        { slot: 'alt', key: 'press', altOffset: 1, tag: 'Other press', options: PRESS_ALT.options },
        BACKEXT, CHINS,
      ]},
    ],
    altAdvance: { press: 'cycle-end', pull: 'per-appearance' },
  },
  {
    id: 'bbp-bbp',
    name: 'Big Push / Big Pull',
    level: 'Intermediate',
    schedule: 'Mon / Tue / Thu weekly',
    blurb: 'Pushing and pulling on separate days: squat and press Monday, deadlift or row Tuesday, the other press Thursday.',
    detail: 'A Big Boy variation that separates pushing and pulling. Monday is the push day: squats with the week’s primary press. Tuesday is the pull day: deadlift alternating with barbell rows, no squats. Thursday is a lighter push session on the other press with assistance — the legs rest until next Monday.',
    progression: 'Squats progress per session; the presses swap Monday/Thursday roles each week; the deadlift and row alternate per appearance. Deload a lift 10% after 3 consecutive failed sessions.',
    days: [
      { label: 'Push', slots: [S3x5, PRESS_ALT, BACKEXT, CHINS] },
      { label: 'Pull', slots: [DL_ROW_ALT, CHINS, BACKEXT] },
      { label: 'Push · Recovery', slots: [
        { slot: 'alt', key: 'press', altOffset: 1, tag: 'Other press', options: PRESS_ALT.options },
        BACKEXT, CHINS,
      ]},
    ],
    altAdvance: { press: 'cycle-end', pull: 'per-appearance' },
  },
  {
    id: 'super-bbb',
    name: 'Super Big Boy',
    level: 'Intermediate',
    schedule: 'Mon / Tue / Wed / Thu weekly',
    blurb: 'The four-day version: squats and heavy pulls twice a week, both presses trained, maximum weekly volume.',
    detail: 'Super Big Boy adds a fourth day for more weekly volume. Monday squats with the primary press; Tuesday is the pull day (deadlift alternating with rows); Wednesday is a lighter session on the other press; Thursday squats again with the next pull in the rotation. Every movement pattern gets hit twice a week.',
    progression: 'Squats progress per session on both squat days; the presses swap roles each week; the deadlift and row alternate per appearance across Tuesday and Thursday. Deload a lift 10% after 3 consecutive failed sessions.',
    days: [
      { label: 'Squat · Press', slots: [S3x5, PRESS_ALT, BACKEXT, CHINS] },
      { label: 'Pull', slots: [DL_ROW_ALT, CHINS, BACKEXT] },
      { label: 'Press · Recovery', slots: [
        { slot: 'alt', key: 'press', altOffset: 1, tag: 'Other press', options: PRESS_ALT.options },
        BACKEXT, CHINS,
      ]},
      { label: 'Squat · Pull', slots: [S3x5, DL_ROW_ALT, CHINS] },
    ],
    altAdvance: { press: 'cycle-end', pull: 'per-appearance' },
  },
];

export function programById(id) {
  return PROGRAMS.find((p) => p.id === id);
}

export function liftsUsed(program) {
  const set = new Set();
  for (const day of program.days) {
    for (const s of day.slots) {
      if (s.options) s.options.forEach((o) => set.add(o.lift));
      else set.add(s.lift);
    }
  }
  return [...set].filter((l) => !LIFTS[l].bodyweight);
}
