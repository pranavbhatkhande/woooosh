// Daily is a date-seeded pick, stable for a given bank of ids.
// Unlimited walks an unseen deck, then restarts oldest-first.

export function fnv1a(text) {
  let hash = 0x811c9dc5;
  const str = String(text);
  for (let i = 0; i < str.length; i += 1) {
    hash ^= str.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

export function dailyPromptIds(ids, date, count = 7) {
  const unique = [...new Set(ids)];
  unique.sort((a, b) => {
    const ha = fnv1a(`${date}|${a}`);
    const hb = fnv1a(`${date}|${b}`);
    if (ha !== hb) return ha < hb ? -1 : 1;
    if (a < b) return -1;
    if (a > b) return 1;
    return 0;
  });
  return unique.slice(0, Math.max(0, count));
}

export function createRng(seed) {
  let state = seed >>> 0;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function shuffle(list, rng) {
  const copy = list.slice();
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rng() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function planUnlimited(allIds, state) {
  const seen = state.seen || {};
  const known = new Set(allIds);
  let deck = (state.deck || []).filter((id) => known.has(id) && !seen[id]);
  const unseen = allIds.filter((id) => !seen[id]);
  if (unseen.length) {
    const inDeck = new Set(deck);
    const missing = unseen.filter((id) => !inDeck.has(id));
    if (missing.length) {
      const seed = (state.seed >>> 0) ^ fnv1a(missing.slice().sort().join("|"));
      deck = deck.concat(shuffle(missing, createRng(seed || 1)));
    }
  } else if (!deck.length) {
    deck = allIds.slice().sort((a, b) => {
      const delta = (seen[a] || 0) - (seen[b] || 0);
      if (delta) return delta;
      if (a < b) return -1;
      if (a > b) return 1;
      return 0;
    });
  }
  return { id: deck[0] || null, deck };
}

export function utcDate(now = new Date()) {
  const date = now instanceof Date ? now : new Date(now);
  return date.toISOString().slice(0, 10);
}

export function previousUtcDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(Date.UTC(y, m - 1, d));
  date.setUTCDate(date.getUTCDate() - 1);
  return date.toISOString().slice(0, 10);
}
