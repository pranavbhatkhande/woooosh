// Pure helpers for the optional AI judge. No network, no Netlify APIs.

import { pointsFor, tierForFamiliarity } from "../../js/tiers.js";
import { normalize } from "../../js/match.js";

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

export function judgeMessages(promptText, answer) {
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
        'Example: for "Name a city in Oregon", Joseph is valid with familiarity 1 or 2, and Portland is valid with familiarity 9 or 10.',
    },
    {
      role: "user",
      content: `Prompt: ${promptText}\nAnswer: ${answer}`,
    },
  ];
}

export function requestBody(mode, model, messages) {
  if (mode === "ollama") {
    return {
      model,
      messages,
      stream: false,
      think: false,
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
