// Pure helpers for the optional AI judge. No network, no Netlify APIs.

import { pointsFor, tierForFamiliarity } from "../../js/tiers.js";
import { exactHit, matchAnswer, normalize, withinOneEdit } from "../../js/match.js";

export const VERDICT_SCHEMA = {
  type: "object",
  additionalProperties: false,
  properties: {
    valid: { type: "boolean" },
    canonical: { type: "string" },
    familiarity: { type: "integer", minimum: 1, maximum: 10 },
    reason: { type: "string" },
  },
  required: ["valid", "canonical", "familiarity", "reason"],
};

const BLOCKED = new Set([
  "fuck",
  "fucking",
  "fucker",
  "motherfucker",
  "shit",
  "shitty",
  "bullshit",
  "cunt",
  "bitch",
  "asshole",
  "dickhead",
  "slut",
  "whore",
  "nigger",
  "nigga",
  "faggot",
  "fag",
  "retard",
  "retarded",
  "spic",
  "kike",
  "chink",
  "gook",
  "wetback",
  "tranny",
  "porn",
  "porno",
]);

export function judgeEndpoint(url, api) {
  const base = String(url || "").trim().replace(/\/+$/, "");
  if (!base) return null;
  const forced = api === "ollama" || api === "openai" ? api : "";
  const mode = forced || (base.endsWith("/api") ? "ollama" : "openai");
  if (mode === "ollama") {
    const root = base.endsWith("/api") ? base.slice(0, -4) : base;
    return { mode, url: `${root}/api/chat` };
  }
  const root = base.endsWith("/v1") ? base.slice(0, -3) : base;
  return { mode, url: `${root}/v1/chat/completions` };
}

export function cacheKey(promptId, answer) {
  const norm = normalize(answer);
  if (!promptId || !norm) return "";
  return `${promptId}__${norm}`;
}

export function validPromptId(id) {
  return typeof id === "string" && /^[a-z0-9][a-z0-9-]{0,48}$/.test(id);
}

export function validAnswer(answer) {
  const text = String(answer ?? "").trim();
  if (!text || text.length > 60) return "";
  if (!normalize(text)) return "";
  if (isBlocked(text)) return "";
  return text;
}

export function isBlocked(text) {
  const norm = normalize(text);
  if (!norm) return false;
  const tokens = norm.split(" ").filter(Boolean);
  if (tokens.some((token) => BLOCKED.has(token))) return true;
  return BLOCKED.has(norm.replace(/ /g, ""));
}

export function allowRequest(hits, now, limit, windowMs) {
  const fresh = (hits || []).filter((stamp) => now - stamp < windowMs);
  if (fresh.length >= limit) return { ok: false, hits: fresh };
  fresh.push(now);
  return { ok: true, hits: fresh };
}

const NEAR_LIMIT = 12;
const ANCHOR_LIMIT = 8;

function editDistance(a, b, max) {
  const la = a.length;
  const lb = b.length;
  if (Math.abs(la - lb) > max) return max + 1;
  let prev = Array.from({ length: lb + 1 }, (_, j) => j);
  let curr = new Array(lb + 1);
  for (let i = 1; i <= la; i += 1) {
    curr[0] = i;
    let best = curr[0];
    const ca = a.charCodeAt(i - 1);
    for (let j = 1; j <= lb; j += 1) {
      const cost = ca === b.charCodeAt(j - 1) ? 0 : 1;
      const value = Math.min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost);
      curr[j] = value;
      if (value < best) best = value;
    }
    if (best > max) return max + 1;
    const swap = prev;
    prev = curr;
    curr = swap;
  }
  return prev[lb];
}

function sharedPrefix(a, b) {
  const n = Math.min(a.length, b.length);
  let i = 0;
  while (i < n && a[i] === b[i]) i += 1;
  return i;
}

function initials(key) {
  const words = key.split(" ").filter(Boolean);
  if (words.length < 2) return "";
  return words.map((word) => word[0]).join("");
}

function scoreKey(norm, key) {
  if (!key || key === norm) return 0;
  const gap = Math.abs(norm.length - key.length);
  if (gap <= 1 && withinOneEdit(norm, key)) return 100;
  if (gap <= 2 && editDistance(norm, key, 2) <= 2) return 86;
  const shorter = Math.min(norm.length, key.length);
  const longer = Math.max(norm.length, key.length);
  if (shorter >= 4 && (key.includes(norm) || norm.includes(key))) return 70 + shorter;
  const words = key.split(" ").filter((word) => word.length >= 2);
  if (words.length >= 2 && norm.length >= 2 && norm.length <= words.length + 1 && initials(key) === norm) return 90;
  const prefix = sharedPrefix(norm, key);
  if (prefix >= 4 && prefix / longer >= 0.45) return 50 + prefix;
  const left = new Set(norm.split(" ").filter((token) => token.length >= 4));
  const shared = key.split(" ").filter((token) => token.length >= 4 && left.has(token)).length;
  if (shared) return 40 + shared * 8;
  return 0;
}

// Near spellings first, then a few obvious bank entries so the model
// knows the category. The model has no web access; this list is the lookup.
export function referenceEntries(compiled, raw) {
  const norm = normalize(raw);
  const answers = compiled && compiled.answers ? compiled.answers : [];
  if (!norm) return [];
  const ranked = [];
  for (const answer of answers) {
    if ((answer.keys || []).includes(norm)) continue;
    let best = 0;
    for (const key of answer.keys || []) best = Math.max(best, scoreKey(norm, key));
    if (best > 0) ranked.push({ answer, best });
  }
  ranked.sort((a, b) => b.best - a.best || a.answer.name.localeCompare(b.answer.name));
  const picked = [];
  const seen = new Set();
  for (const row of ranked) {
    if (picked.length >= NEAR_LIMIT) break;
    if (seen.has(row.answer.name)) continue;
    seen.add(row.answer.name);
    picked.push(row.answer);
  }
  const anchors = [];
  for (const answer of answers) {
    if (anchors.length >= ANCHOR_LIMIT) break;
    if (answer.tier !== "taxi" || seen.has(answer.name)) continue;
    seen.add(answer.name);
    anchors.push(answer);
  }
  return picked.concat(anchors);
}

function referenceLine(entry) {
  if (!entry) return "";
  if (typeof entry === "string") return entry.trim().slice(0, 80);
  const name = String(entry.name || "").trim().slice(0, 80);
  if (!name) return "";
  const aliases = (entry.aliases || [])
    .map((alias) => String(alias || "").trim().slice(0, 40))
    .filter(Boolean)
    .slice(0, 2);
  return aliases.length ? `${name} (also ${aliases.join(", ")})` : name;
}

export function judgeMessages(promptText, answer, references = []) {
  const lines = [];
  let used = 0;
  for (const entry of references || []) {
    if (lines.length >= 20) break;
    const line = referenceLine(entry);
    if (!line) continue;
    if (used + line.length > 4000) break;
    lines.push(`- ${line}`);
    used += line.length;
  }
  const lookup = lines.length
    ? `\nReference entries:\n${lines.join("\n")}\n` +
      "If the answer is a typo, misspelling, plural, missing article, accent difference, abbreviation, or alternate or partial name of a reference entry, set canonical to that entry's name exactly as written before the parentheses. " +
      "If it is a real member of the category that is not in the list, valid is true and canonical is its usual English name. " +
      "If it is the wrong category, too vague, or not a real member, valid is false and canonical is an empty string.\n"
    : "";
  return [
    {
      role: "system",
      content:
        "You judge one short answer to a category prompt. Reply with JSON only. " +
        "Decide validity and familiarity separately. " +
        "valid is true when the answer is a real, specific member of the category, " +
        "including obscure, small, local, historical, or specialist examples. " +
        "Not being famous does not make it invalid. " +
        "valid is false only when it is the wrong category, too vague to be one member, " +
        "or not a real member of that category. " +
        "familiarity is 10 when almost everyone knows it and 1 or 2 when only specialists or locals do. " +
        "An obscure real member stays valid and gets a low familiarity. " +
        "canonical is the usual English name, or an empty string when invalid. " +
        "Be lenient about near-misses of real members: typos, misspellings, alternate or partial names, plurals, missing articles, accents, and abbreviations. " +
        "When a reference entry is the intended answer, canonical must be that entry's name, copied exactly. " +
        'Example: for "Name a city in Oregon", Joseph is valid with familiarity 1 or 2, and Portland is valid with familiarity 9 or 10.',
    },
    {
      role: "user",
      content: `Prompt: ${promptText}\nAnswer: ${answer}${lookup}`,
    },
  ];
}

// Exact bank hits score here with no verdict. A null verdict means the model
// never answered, so the bank's fuzzy match is the fallback. A verdict with
// valid false is a real reject and does not fall through to fuzzy matching.
export function settleJudged(compiled, answer, verdict) {
  const exact = exactHit(compiled, answer);
  if (exact) return scoreJudged(null, exact);
  if (!verdict) {
    const fuzzy = matchAnswer(compiled, answer);
    return fuzzy ? scoreJudged(null, fuzzy) : { valid: false, inBank: false, judged: false };
  }
  if (!verdict.valid || isBlocked(verdict.canonical)) {
    return { valid: false, inBank: false, judged: false };
  }
  const fromCanonical = verdict.canonical ? matchAnswer(compiled, verdict.canonical) : null;
  const fromTyped = matchAnswer(compiled, answer);
  return scoreJudged(verdict, fromCanonical || fromTyped);
}

export function requestBody(mode, model, messages) {
  if (mode === "ollama") {
    return {
      model,
      messages,
      stream: false,
      think: false,
      keep_alive: "30m",
      format: VERDICT_SCHEMA,
      options: { temperature: 0.1, num_predict: 300 },
    };
  }
  return {
    model,
    messages,
    temperature: 0.1,
    max_tokens: 300,
    think: false,
    response_format: {
      type: "json_schema",
      json_schema: { name: "verdict", strict: true, schema: VERDICT_SCHEMA },
    },
  };
}

export function withoutThink(body) {
  const copy = { ...body };
  delete copy.think;
  return copy;
}

export function parseVerdict(text) {
  if (!text || typeof text !== "string") return null;
  let raw = text.trim();
  const fenced = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
  if (fenced) raw = fenced[1].trim();
  const start = raw.indexOf("{");
  const end = raw.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  let data;
  try {
    data = JSON.parse(raw.slice(start, end + 1));
  } catch {
    return null;
  }
  if (!data || typeof data.valid !== "boolean") return null;
  const familiarity = Math.round(Number(data.familiarity));
  if (!Number.isFinite(familiarity)) return null;
  return {
    valid: data.valid,
    canonical: String(data.canonical || "").trim().slice(0, 60),
    familiarity: Math.max(1, Math.min(10, familiarity)),
    reason: String(data.reason || "").trim().slice(0, 240),
  };
}

export function messageText(payload) {
  if (!payload || typeof payload !== "object") return "";
  if (payload.message && typeof payload.message.content === "string") return payload.message.content;
  const choice = Array.isArray(payload.choices) ? payload.choices[0] : null;
  const content = choice && choice.message ? choice.message.content : "";
  return typeof content === "string" ? content : "";
}

// Bank hits keep their real tier, including the gem. Anything the model
// accepts is capped below ESCAPE.
export function scoreJudged(verdict, bankHit) {
  if (bankHit) {
    return {
      valid: true,
      inBank: true,
      judged: false,
      canonical: bankHit.name,
      tier: bankHit.tier,
      gem: Boolean(bankHit.gem),
      points: pointsFor(bankHit.tier),
    };
  }
  if (!verdict || !verdict.valid || isBlocked(verdict.canonical)) {
    return { valid: false, inBank: false, judged: false };
  }
  const tier = tierForFamiliarity(verdict.familiarity);
  if (!tier || tier === "escape") return { valid: false, inBank: false, judged: false };
  const canonical = String(verdict.canonical || "").trim().slice(0, 60);
  if (!canonical) return { valid: false, inBank: false, judged: false };
  return {
    valid: true,
    inBank: false,
    judged: true,
    canonical,
    tier,
    gem: false,
    points: pointsFor(tier),
    familiarity: verdict.familiarity,
    reason: verdict.reason || "",
  };
}

export function clientIp(headers) {
  const bag = headers || {};
  const read = (name) => bag[name] || bag[name.toLowerCase()] || "";
  const direct = read("x-nf-client-connection-ip");
  if (direct) return String(direct).slice(0, 80);
  const forwarded = String(read("x-forwarded-for")).split(",")[0].trim();
  return (forwarded || "unknown").slice(0, 80);
}
