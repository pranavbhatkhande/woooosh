/**
 * Forgiving answer match.
 * Case, accents, punctuation, and one leading a/an/the are ignored.
 * "&" and "and" match. Simple plurals match. One edit (including a
 * transposition) is allowed on longer keys, unless two answers are that
 * close — those stay exact-only so a typo cannot land on the wrong one.
 */

const EXCEPTIONS = new Set([
  "species",
  "series",
  "news",
  "maths",
  "lens",
  "mess",
  "atlas",
  "chaos",
  "metropolis",
  "epidermis",
  "alias",
  "gas",
  "bus",
  "this",
  "plus",
]);

export function foldAccents(value) {
  return value
    .replace(/æ/g, "ae")
    .replace(/œ/g, "oe")
    .replace(/ø/g, "o")
    .replace(/ł/g, "l")
    .replace(/ß/g, "ss")
    .replace(/đ/g, "d")
    .replace(/þ/g, "th")
    .replace(/ð/g, "d")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "");
}

export function normalize(raw) {
  if (raw == null) return "";
  let text = foldAccents(String(raw)).toLowerCase();
  text = text.replace(/&/g, " and ").replace(/\+/g, " and ");
  text = text.replace(/['’]/g, "");
  text = text.replace(/[\u2010-\u2015\-_/]+/g, " ");
  text = text.replace(/[^a-z0-9\s]/g, " ");
  text = text.replace(/\s+/g, " ").trim();
  const article = text.match(/^(?:the|a|an)\s+(.+)$/);
  if (article) text = article[1];
  return text;
}

function wordVariants(word) {
  if (!word || word.length <= 3 || EXCEPTIONS.has(word)) return [];
  const variants = [];
  if (word.endsWith("ies") && word.length > 4) {
    variants.push(word.slice(0, -3) + "y");
  }
  if (/(?:ches|shes|xes|zes|sses|ses)$/.test(word) && word.length > 4) {
    variants.push(word.slice(0, -2));
  }
  if (/[^aeiou]s$/.test(word) && !word.endsWith("ss")) {
    variants.push(word.slice(0, -1));
  }
  // horses → horse, movies → movie, games → game. "paris" does not end in "es".
  if (word.endsWith("es") && word.length > 4) {
    const stem = word.slice(0, -1);
    if (stem.endsWith("e")) variants.push(stem);
  }
  return variants.filter((variant) => variant && variant !== word && variant.length >= 2);
}

export function candidates(phrase) {
  const forms = new Set();
  if (!phrase) return forms;
  forms.add(phrase);
  const parts = phrase.split(" ");
  const word = parts[parts.length - 1];
  for (const variant of wordVariants(word)) {
    const next = parts.slice(0, -1).concat(variant).join(" ");
    if (next) forms.add(next);
  }
  return forms;
}

/** True when one insertion, deletion, substitution, or adjacent swap apart. */
export function withinOneEdit(a, b) {
  if (a === b) return true;
  const la = a.length;
  const lb = b.length;
  if (Math.abs(la - lb) > 1) return false;
  if (la === lb) {
    let i = 0;
    for (; i < la; i += 1) {
      if (a[i] !== b[i]) break;
    }
    if (i === la) return true;
    if (i + 1 < la && a[i] === b[i + 1] && a[i + 1] === b[i]) {
      for (let j = i + 2; j < la; j += 1) {
        if (a[j] !== b[j]) return false;
      }
      return true;
    }
    for (let j = i + 1; j < la; j += 1) {
      if (a[j] !== b[j]) return false;
    }
    return true;
  }
  const shorter = la < lb ? a : b;
  const longer = la < lb ? b : a;
  let i = 0;
  let j = 0;
  let skipped = 0;
  while (i < shorter.length && j < longer.length) {
    if (shorter[i] === longer[j]) {
      i += 1;
      j += 1;
    } else {
      skipped += 1;
      if (skipped > 1) return false;
      j += 1;
    }
  }
  return true;
}

function formsShare(left, right) {
  for (const form of left) {
    if (right.has(form)) return true;
  }
  return false;
}

export function prepareAnswers(answers) {
  const entries = [];
  for (const answer of answers || []) {
    const keys = [answer.name, ...(answer.aliases || [])];
    const seen = new Set();
    for (const key of keys) {
      const norm = normalize(key);
      if (!norm || seen.has(norm)) continue;
      seen.add(norm);
      entries.push({
        key: norm,
        forms: candidates(norm),
        name: answer.name,
        tier: answer.tier,
        gem: Boolean(answer.gem),
      });
    }
  }

  const typoKeys = [];
  for (let i = 0; i < entries.length; i += 1) {
    const entry = entries[i];
    if (entry.key.length < 6) continue;
    let neighbor = false;
    for (let j = 0; j < entries.length; j += 1) {
      if (i === j || entries[j].name === entry.name) continue;
      if (Math.abs(entries[j].key.length - entry.key.length) > 1) continue;
      if (entries[j].key.length < 6) continue;
      if (withinOneEdit(entry.key, entries[j].key)) {
        neighbor = true;
        break;
      }
    }
    if (!neighbor) typoKeys.push(entry);
  }

  return { entries, typoKeys };
}

function hitFrom(entry, via) {
  return { name: entry.name, tier: entry.tier, gem: entry.gem, via };
}

export function matchAnswer(raw, answers, prepared = null) {
  const input = normalize(raw);
  if (!input) return null;
  const prep = prepared || prepareAnswers(answers);
  const inputForms = candidates(input);

  const exact = [];
  const plural = [];
  for (const entry of prep.entries) {
    if (entry.key === input) {
      exact.push(entry);
      continue;
    }
    if (formsShare(inputForms, entry.forms)) plural.push(entry);
  }

  const exactNames = unique(exact);
  if (exactNames.length >= 1) return hitFrom(exactNames[0], "exact");

  const pluralNames = unique(plural);
  if (pluralNames.length === 1) return hitFrom(pluralNames[0], "plural");
  if (pluralNames.length > 1) return null;

  if (input.length < 6) return null;
  const typo = [];
  for (const entry of prep.typoKeys) {
    if (withinOneEdit(input, entry.key)) typo.push(entry);
  }
  const typoNames = unique(typo);
  if (typoNames.length === 1) return hitFrom(typoNames[0], "typo");
  return null;
}

function unique(entries) {
  const byName = new Map();
  for (const entry of entries) {
    if (!byName.has(entry.name)) byName.set(entry.name, entry);
  }
  return [...byName.values()];
}
