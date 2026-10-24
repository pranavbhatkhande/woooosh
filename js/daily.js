import { RUN_LENGTH } from "./constants.js";

export function todayUTC(now = new Date()) {
  return now.toISOString().slice(0, 10);
}

export function shiftDate(iso, days) {
  const [year, month, day] = iso.split("-").map(Number);
  const date = new Date(Date.UTC(year, month - 1, day));
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

export function formatDailyDate(iso) {
  const [year, month, day] = iso.split("-").map(Number);
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  if (!year || !month || !day) return iso;
  return `${day} ${months[month - 1]} ${year}`;
}

export function hashString(value) {
  let hash = 2166136261;
  const text = String(value);
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

export function mulberry32(seed) {
  let state = seed >>> 0;
  return function rng() {
    state = (state + 0x6d2b79f5) | 0;
    let mixed = Math.imul(state ^ (state >>> 15), 1 | state);
    mixed = (mixed + Math.imul(mixed ^ (mixed >>> 7), 61 | mixed)) ^ mixed;
    return ((mixed ^ (mixed >>> 14)) >>> 0) / 4294967296;
  };
}

export function fallbackDailyIds(ids, date, count = RUN_LENGTH) {
  const pool = [...ids].sort();
  const rng = mulberry32(hashString(`woooosh-daily:${date}`));
  for (let i = pool.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rng() * (i + 1));
    const swap = pool[i];
    pool[i] = pool[j];
    pool[j] = swap;
  }
  return pool.slice(0, Math.min(count, pool.length));
}

export function idsForDate(schedule, ids, date, count = RUN_LENGTH) {
  const known = new Set(ids);
  const listed = schedule?.dates?.[date];
  if (Array.isArray(listed) && listed.length === count && listed.every((id) => known.has(id))) {
    return listed.slice();
  }
  return fallbackDailyIds(ids, date, count);
}
