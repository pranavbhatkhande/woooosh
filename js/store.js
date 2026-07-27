const KEY = 'ss-tracker-v1';

export function load() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function save(state) {
  localStorage.setItem(KEY, JSON.stringify(state));
}

export function freshState(programId, units, starts, defaults) {
  const lifts = {};
  for (const [lift, weight] of Object.entries(starts)) {
    lifts[lift] = { weight, increment: defaults.increment[lift] ?? defaults.increment.press, fails: 0 };
  }
  return {
    version: 1,
    settings: {
      units,
      barWeight: defaults.bar,
      plates: [...defaults.plates],
      theme: 'auto',
    },
    program: { id: programId, dayIndex: 0, alt: {}, startedAt: new Date().toISOString() },
    lifts,
    history: [],
    active: null,
  };
}

export function exportJSON(state) {
  const blob = new Blob([JSON.stringify(state, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `starting-strength-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

export function importJSON(file) {
  return file.text().then((text) => {
    const data = JSON.parse(text);
    if (!data.settings || !data.program || !data.lifts) throw new Error('Not a Starting Strength backup file');
    return data;
  });
}
