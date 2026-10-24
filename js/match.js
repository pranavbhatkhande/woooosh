// Answer matching for WOOOOSH.
// Case, accents, punctuation, leading articles, ampersands, simple plurals,
// aliases, and a single-edit typo — unless that typo could be two answers.

const ARTICLE = /^(?:a|an|the)\s+/;

export function normalize(raw) {
  let s = String(raw ?? "").trim().toLowerCase();
  if (!s) return "";
  s = s.replace(/c\+\+/g, "c plus plus");
  s = s.replace(/c#/g, "c sharp");
  s = s.replace(/f#/g, "f sharp");
  s = s.replace(/\br\s*&\s*b\b/g, "r and b");
  s = s.replace(/\s+&\s+/g, " and ");
  s = s.replace(/\s+&/g, " and ");
  s = s.replace(/&\s+/g, " and ");
  s = s.replace(/&/g, "");
  s = s
    .replace(/ß/g, "ss")
    .replace(/æ/g, "ae")
    .replace(/œ/g, "oe")
    .replace(/ø/g, "o")
    .replace(/ł/g, "l")
    .replace(/đ/g, "d")
    .replace(/þ/g, "th");
  s = s.normalize("NFD").replace(/\p{M}/gu, "");
  s = s.replace(/['’]/g, "");
  s = s.replace(/[‐‑‒–—-]/g, " ");
  s = s.replace(/[^\p{L}\p{N}\s]/gu, "");
  s = s.replace(/\s+/g, " ").trim();
  while (ARTICLE.test(s)) s = s.replace(ARTICLE, "");
  return s.trim();
}

export function variants(norm) {
  const out = new Set();
  if (!norm || norm.length < 4) return out;
  const add = (v) => {
    if (v && v !== norm && v.length >= 2) out.add(v);
  };
  if (norm.endsWith("s") && !norm.endsWith("ss")) add(norm.slice(0, -1));
  if (norm.endsWith("es")) add(norm.slice(0, -2));
  if (norm.endsWith("ies")) add(norm.slice(0, -3) + "y");
  if (/[^aeiou]y$/.test(norm)) add(norm.slice(0, -1) + "ies");
  else if (/(?:s|x|z|ch|sh)$/.test(norm)) add(norm + "es");
  else if (!norm.endsWith("s")) add(norm + "s");
  return out;
}

function keysFor(answer) {
  const keys = new Set();
  const raws = [answer.name, ...(answer.aliases || [])];
  for (const raw of raws) {
    const n = normalize(raw);
    if (!n) continue;
    keys.add(n);
    const compact = n.replace(/\s+/g, "");
    if (compact.length >= 7 && compact !== n) keys.add(compact);
  }
  return [...keys];
}

export function compileAnswers(answers) {
  const prepared = (answers || []).map((answer) => ({
    name: answer.name,
    aliases: answer.aliases || [],
    tier: answer.tier,
    gem: Boolean(answer.gem),
    keys: keysFor(answer),
  }));
  const exact = new Map();
  for (const answer of prepared) {
    for (const key of answer.keys) {
      if (!exact.has(key)) exact.set(key, answer);
      else if (exact.get(key) !== answer) exact.set(key, null);
    }
  }
  return { answers: prepared, exact };
}

function uniqueAnswers(list) {
  const seen = new Set();
  const out = [];
  for (const answer of list) {
    if (!answer || seen.has(answer.name)) continue;
    seen.add(answer.name);
    out.push(answer);
  }
  return out;
}

// Edit distance <= 1, with an adjacent transposition counting as one edit.
export function withinOneEdit(a, b) {
  if (a === b) return true;
  const la = a.length;
  const lb = b.length;
  if (Math.abs(la - lb) > 1) return false;
  if (la === lb) {
    let diff = -1;
    for (let i = 0; i < la; i += 1) {
      if (a[i] !== b[i]) {
        if (diff >= 0) {
          if (i === diff + 1 && a[diff] === b[i] && a[i] === b[diff]) {
            for (let k = i + 1; k < la; k += 1) if (a[k] !== b[k]) return false;
            return true;
          }
          return false;
        }
        diff = i;
      }
    }
    return diff >= 0;
  }
  const [short, long] = la < lb ? [a, b] : [b, a];
  let i = 0;
  let j = 0;
  let skipped = false;
  while (i < short.length && j < long.length) {
    if (short[i] === long[j]) {
      i += 1;
      j += 1;
    } else if (skipped) return false;
    else {
      skipped = true;
      j += 1;
    }
  }
  return true;
}

function fuzzyHits(compiled, token) {
  if (!token || token.length < 6) return [];
  const hits = [];
  for (const answer of compiled.answers) {
    for (const key of answer.keys) {
      if (key.length < 6) continue;
      if (key !== token && withinOneEdit(token, key)) {
        hits.push(answer);
        break;
      }
    }
  }
  return uniqueAnswers(hits);
}

// Exact or normalized key only: the display name, an alias, or a compact
// spelling already stored on the answer. Plurals and typos are not exact.
export function exactHit(compiled, raw) {
  if (!compiled) return null;
  const norm = normalize(raw);
  if (!norm || !compiled.exact.has(norm)) return null;
  return compiled.exact.get(norm);
}

export function matchAnswer(compiled, raw) {
  if (!compiled) return null;
  const norm = normalize(raw);
  if (!norm) return null;
  if (compiled.exact.has(norm)) return compiled.exact.get(norm);

  const morph = [];
  for (const variant of variants(norm)) {
    if (!compiled.exact.has(variant)) continue;
    const hit = compiled.exact.get(variant);
    if (hit) morph.push(hit);
  }
  const morphHits = uniqueAnswers(morph);
  if (morphHits.length === 1) return morphHits[0];
  if (morphHits.length > 1) return null;

  const directFuzzy = fuzzyHits(compiled, norm);
  if (directFuzzy.length === 1) return directFuzzy[0];
  if (directFuzzy.length > 1) return null;

  const variantFuzzy = [];
  for (const variant of variants(norm)) {
    variantFuzzy.push(...fuzzyHits(compiled, variant));
  }
  const variantHits = uniqueAnswers(variantFuzzy);
  if (variantHits.length === 1) return variantHits[0];
  return null;
}
