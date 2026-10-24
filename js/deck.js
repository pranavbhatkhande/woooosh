/** Unlimited deck: unseen prompts first, then oldest-seen first. */

export function shuffle(list, rng) {
  const copy = [...list];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rng() * (i + 1));
    const swap = copy[i];
    copy[i] = copy[j];
    copy[j] = swap;
  }
  return copy;
}

export function createDeck(ids, rng = Math.random) {
  return {
    seenOrder: [],
    remaining: shuffle(ids, rng),
    cycle: 1,
  };
}

function recycleOldestFirst(seenOrder, allIds) {
  const firstSeen = new Map();
  seenOrder.forEach((id, index) => {
    if (!firstSeen.has(id)) firstSeen.set(id, index);
  });
  const known = new Set(allIds);
  const old = [...firstSeen.entries()]
    .filter(([id]) => known.has(id))
    .sort((a, b) => a[1] - b[1])
    .map(([id]) => id);
  const fresh = allIds.filter((id) => !firstSeen.has(id));
  return fresh.concat(old);
}

/**
 * Draw `count` prompt ids. A prompt is not repeated until every prompt
 * in the bank has been seen; the replay starts with the oldest.
 * Prompts added to the bank since the last run are treated as unseen.
 */
export function takeRun(deck, allIds, count, rng = Math.random) {
  const seen = new Set(deck.seenOrder);
  let remaining = (deck.remaining || []).filter((id) => allIds.includes(id));
  const inRemaining = new Set(remaining);
  const fresh = allIds.filter((id) => !seen.has(id) && !inRemaining.has(id));
  const unseenRemaining = remaining.filter((id) => !seen.has(id));
  const seenRemaining = remaining.filter((id) => seen.has(id));
  remaining = shuffle(fresh, rng).concat(unseenRemaining, seenRemaining);

  const picked = [];
  let cycle = deck.cycle || 1;
  while (picked.length < count) {
    if (remaining.length === 0) {
      const recycled = recycleOldestFirst(deck.seenOrder.concat(picked), allIds)
        .filter((id) => !picked.includes(id));
      if (recycled.length === 0) break;
      remaining = recycled;
      cycle += 1;
    }
    picked.push(remaining.shift());
  }

  return {
    ids: picked,
    deck: {
      seenOrder: deck.seenOrder.concat(picked),
      remaining,
      cycle,
    },
  };
}
