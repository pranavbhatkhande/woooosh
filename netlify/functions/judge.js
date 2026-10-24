// The public site scores from the static bank only. This function stays
// inert even when JUDGE_URL is set, so a miss never calls a model.

import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { compileAnswers, matchAnswer } from "../../js/match.js";
import {
  allowRequest,
  cacheKey,
  clientIp,
  judgeEndpoint,
  judgeMessages,
  messageText,
  parseVerdict,
  requestBody,
  scoreJudged,
  validAnswer,
  validPromptId,
  withoutThink,
} from "../lib/judge-core.js";

// Netlify's esbuild bundle is CommonJS, so import.meta.url can be missing.
// fileURLToPath(undefined) throws while the module is loading, which would
// 502 even the "judge disabled" response.
function moduleDir() {
  try {
    const url = import.meta.url;
    if (!url) return "";
    return path.dirname(fileURLToPath(url));
  } catch {
    return "";
  }
}

const HERE = moduleDir();
const ROOTS = [
  process.cwd(),
  HERE ? path.resolve(HERE, "../..") : "",
  process.env.LAMBDA_TASK_ROOT || "",
  "/var/task",
].filter(Boolean);

const IP_LIMIT = 30;
const GLOBAL_LIMIT = 120;
const WINDOW_MS = 60_000;
const UPSTREAM_MS = 3500;

function state() {
  if (!globalThis.__wooooshJudge) {
    globalThis.__wooooshJudge = { ip: new Map(), global: [], verdicts: new Map() };
  }
  return globalThis.__wooooshJudge;
}

function json(status, body) {
  return {
    statusCode: status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
    body: JSON.stringify(body),
  };
}

function enabled() {
  // Hard off. Do not consult JUDGE_URL. The bank is the only scorer.
  return false;
}

async function readJsonFile(rel) {
  for (const root of ROOTS) {
    try {
      const text = await readFile(path.join(root, rel), "utf8");
      return JSON.parse(text);
    } catch {
      // The next root may be the one Netlify bundled.
    }
  }
  return null;
}

function originOf(event) {
  const headers = event.headers || {};
  const host = headers.host || headers.Host;
  if (!host) return "";
  const proto = headers["x-forwarded-proto"] || headers["X-Forwarded-Proto"] || "https";
  return `${proto}://${host}`;
}

async function fetchJson(origin, rel) {
  if (!origin) return null;
  try {
    const response = await fetch(`${origin}/${rel.replace(/^\//, "")}`);
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

async function loadIndex(event) {
  const cached = state().index;
  if (cached) return cached;
  const index = (await readJsonFile("data/index.json")) || (await fetchJson(originOf(event), "data/index.json"));
  if (index) state().index = index;
  return index;
}

async function loadPrompt(event, promptId) {
  const memory = state().prompts || (state().prompts = new Map());
  if (memory.has(promptId)) return memory.get(promptId);
  const index = await loadIndex(event);
  if (!index) return null;
  const shard = (index.shards || []).find((entry) => (entry.ids || []).includes(promptId));
  if (!shard) return null;
  const loaded = state().shards || (state().shards = new Map());
  let prompts = loaded.get(shard.file);
  if (!prompts) {
    prompts = (await readJsonFile(shard.file)) || (await fetchJson(originOf(event), shard.file));
    if (!prompts) return null;
    loaded.set(shard.file, prompts);
  }
  const prompt = prompts.find((entry) => entry.id === promptId) || null;
  if (prompt) memory.set(promptId, prompt);
  return prompt;
}

async function blobStore(name) {
  try {
    const { getStore } = await import("@netlify/blobs");
    return getStore(name);
  } catch {
    return null;
  }
}

async function blobGet(store, key) {
  if (!store) return null;
  try {
    return await store.get(key, { type: "json" });
  } catch {
    return null;
  }
}

async function blobSet(store, key, value) {
  if (!store) return;
  try {
    if (typeof store.setJSON === "function") await store.setJSON(key, value);
    else await store.set(key, JSON.stringify(value));
  } catch {
    // A cache miss only costs another model call. Don't fail the player.
  }
}

function remember(key, verdict) {
  const bag = state().verdicts;
  bag.set(key, verdict);
  if (bag.size > 500) {
    const oldest = bag.keys().next().value;
    bag.delete(oldest);
  }
}

async function callModel(answer, promptText) {
  const endpoint = judgeEndpoint(process.env.JUDGE_URL, process.env.JUDGE_API || "");
  if (!endpoint) throw new Error("no endpoint");
  const model = process.env.JUDGE_MODEL || "qwen3.8:27b";
  const messages = judgeMessages(promptText, answer);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), UPSTREAM_MS);
  const headers = { "Content-Type": "application/json" };
  if (process.env.JUDGE_TOKEN) headers.Authorization = `Bearer ${process.env.JUDGE_TOKEN}`;
  try {
    return await postUpstream(endpoint.url, requestBody(endpoint.mode, model, messages), headers, controller.signal);
  } catch (error) {
    const message = String(error && error.detail ? error.detail : error && error.message ? error.message : error);
    if (!/think/i.test(message)) throw error;
    return await postUpstream(endpoint.url, withoutThink(requestBody(endpoint.mode, model, messages)), headers, controller.signal);
  } finally {
    clearTimeout(timer);
  }
}

async function postUpstream(url, body, headers, signal) {
  const response = await fetch(url, { method: "POST", headers, body: JSON.stringify(body), signal });
  const text = await response.text();
  if (!response.ok) {
    const error = new Error(`upstream ${response.status}`);
    error.detail = text.slice(0, 300);
    throw error;
  }
  let payload;
  try {
    payload = JSON.parse(text);
  } catch {
    payload = { message: { content: text } };
  }
  const verdict = parseVerdict(messageText(payload));
  if (!verdict) throw new Error("unparsed verdict");
  return verdict;
}

function readJsonBody(event) {
  if (!event || !event.body) return {};
  const raw = event.isBase64Encoded ? Buffer.from(event.body, "base64").toString("utf8") : event.body;
  return JSON.parse(raw);
}

export async function handler(event) {
  if (!enabled()) return json(200, { enabled: false });
  if (event.httpMethod === "GET") return json(200, { enabled: true });
  if (event.httpMethod !== "POST") return json(405, { enabled: true, error: "method" });

  let body;
  try {
    body = readJsonBody(event);
  } catch {
    return json(400, { enabled: true, error: "json" });
  }
  const promptId = body.promptId;
  const answer = validAnswer(body.answer);
  if (!validPromptId(promptId) || !answer) return json(400, { enabled: true, error: "input" });

  const now = Date.now();
  const bag = state();
  const ip = clientIp(event.headers);
  const ipHits = bag.ip.get(ip) || [];
  const ipResult = allowRequest(ipHits, now, IP_LIMIT, WINDOW_MS);
  bag.ip.set(ip, ipResult.hits);
  const globalResult = allowRequest(bag.global, now, GLOBAL_LIMIT, WINDOW_MS);
  bag.global = globalResult.hits;
  if (!ipResult.ok || !globalResult.ok) return json(429, { enabled: true, error: "rate" });

  const prompt = await loadPrompt(event, promptId);
  if (!prompt) return json(404, { enabled: true, error: "prompt" });

  const compiled = compileAnswers(prompt.answers);
  const direct = matchAnswer(compiled, answer);
  if (direct) return json(200, { enabled: true, ...scoreJudged(null, direct) });

  const key = cacheKey(promptId, answer);
  if (bag.verdicts.has(key)) return json(200, { enabled: true, ...bag.verdicts.get(key) });
  const store = await blobStore("judge-verdicts");
  const cached = await blobGet(store, key);
  if (cached && typeof cached === "object" && "valid" in cached) {
    remember(key, cached);
    return json(200, { enabled: true, ...cached });
  }

  let verdict;
  try {
    verdict = await callModel(answer, prompt.text);
  } catch {
    return json(502, { enabled: true, error: "upstream" });
  }
  const fromCanonical = verdict.canonical ? matchAnswer(compiled, verdict.canonical) : null;
  const scored = scoreJudged(verdict, fromCanonical);
  remember(key, scored);
  await blobSet(store, key, scored);
  if (scored.judged) {
    const accepted = await blobStore("judge-accepted");
    await blobSet(accepted, key, {
      promptId,
      answer,
      canonical: scored.canonical,
      tier: scored.tier,
      familiarity: scored.familiarity,
      reason: scored.reason || "",
      at: new Date().toISOString(),
    });
  }
  return json(200, { enabled: true, ...scored });
}
