"""Curate prompts with a local Ollama or OpenAI-compatible model.

The seed bank does not depend on this. It is for the owner's machine, where
Ollama serves qwen3.8:27b. Raw replies are cached so a run can resume, and
tiers come from percentile rank so a flat familiarity spread still fills.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

from pipeline.net import CACHE
from pipeline.normalize import normalize
from pipeline.profanity import is_profane
from pipeline.publish import load_published
from pipeline.quality import publishable
from pipeline.tiers import assign_by_popularity, popularity_score

try:
    from wordfreq import zipf_frequency
except ImportError:  # pragma: no cover - optional at runtime
    zipf_frequency = None

ROOT = Path(__file__).resolve().parents[1]
WORK = CACHE / "llm"
RAW = WORK / "raw"
ACCEPTED = CACHE / "accepted"
DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3.8:27b"
SLUG = re.compile(r"[^a-z0-9]+")
VERBOSE = False

STOPWORDS = {
    "name",
    "a",
    "an",
    "the",
    "type",
    "kind",
    "style",
    "of",
    "common",
    "famous",
    "in",
    "from",
    "with",
    "our",
    "that",
    "you",
}
TINY_PHRASES = (
    "solar system",
    "day of the week",
    "days of the week",
    "state capital",
    "months of the year",
    "the alphabet",
)
TINY_WORDS = {
    "planet",
    "planets",
    "continent",
    "continents",
    "ocean",
    "oceans",
    "month",
    "months",
    "weekday",
    "weekdays",
}

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "aliases": {"type": "array", "items": {"type": "string"}},
                    "familiarity": {"type": "integer"},
                },
                "required": ["name", "familiarity"],
            },
        }
    },
    "required": ["answers"],
}
IDEA_SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "category": {"type": "string"},
                },
                "required": ["text", "category"],
            },
        }
    },
    "required": ["ideas"],
}
KEEP_SCHEMA = {
    "type": "object",
    "properties": {"keep": {"type": "array", "items": {"type": "string"}}},
    "required": ["keep"],
}


def _env_url() -> str:
    return (os.environ.get("PIPELINE_LLM_URL") or DEFAULT_URL).rstrip("/")


def _env_model() -> str:
    return os.environ.get("PIPELINE_LLM_MODEL") or DEFAULT_MODEL


def endpoint(base: str | None = None) -> tuple[str, str]:
    """Return (mode, url). mode is ollama or openai."""
    raw = (base or _env_url()).rstrip("/")
    if raw.endswith("/api"):
        return "ollama", f"{raw[:-4]}/api/chat"
    if raw.endswith("/v1"):
        return "openai", f"{raw}/chat/completions"
    if os.environ.get("PIPELINE_LLM_API") == "openai":
        return "openai", f"{raw}/v1/chat/completions"
    return "ollama", f"{raw}/api/chat"


def _payload(mode: str, model: str, messages: list[dict], schema: dict | None, num_predict: int) -> dict:
    if mode == "ollama":
        body = {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"temperature": 0.4, "num_predict": num_predict},
        }
        if schema is not None:
            body["format"] = schema
        return body
    body = {
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": num_predict,
        "think": False,
    }
    if schema is not None:
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "result", "schema": schema},
        }
    else:
        body["response_format"] = {"type": "json_object"}
    return body


def parse_json_lenient(text: str) -> dict:
    """Pull one JSON object out of a model reply, including a trailing comma."""
    raw = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fenced:
        raw = fenced.group(1).strip()
    start = raw.find("{")
    if start < 0:
        raise ValueError("model did not return a JSON object")
    snippet = re.sub(r",\s*([}\]])", r"\1", raw[start:])
    try:
        data, _ = json.JSONDecoder().raw_decode(snippet)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSONDecodeError: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("model JSON was not an object")
    return data


def _parse_json(text: str) -> dict:
    return parse_json_lenient(text)


def _cache_key(model: str, messages: list[dict], schema: dict | None) -> str:
    blob = json.dumps({"model": model, "messages": messages, "schema": schema}, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _read_cached(key: str) -> dict | None:
    path = RAW / f"{key}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError:
        return None
    parsed = data.get("parsed")
    if isinstance(parsed, dict):
        return parsed
    return None


def _write_cache(key: str, raw: str, parsed: dict | None, error: str) -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    (RAW / f"{key}.json").write_text(
        json.dumps({"raw": raw, "parsed": parsed, "error": error}, ensure_ascii=False)
    )


def _message_text(payload: dict) -> str:
    if isinstance(payload.get("message"), dict):
        return str(payload["message"].get("content") or "")
    choices = payload.get("choices") or []
    if choices:
        return str((choices[0].get("message") or {}).get("content") or "")
    return ""


def _post(body: dict, timeout: int) -> str:
    mode, url = endpoint()
    encoded = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("PIPELINE_LLM_TOKEN") or ""
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=encoded, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        if "think" in detail.lower() and "think" in body:
            retry = dict(body)
            retry.pop("think", None)
            return _post(retry, timeout)
        raise RuntimeError(f"llm http {exc.code}: {detail}") from exc
    return _message_text(payload)


def chat_json(
    messages: list[dict],
    *,
    schema: dict | None = None,
    timeout: int = 180,
    num_predict: int = 4096,
) -> dict:
    model = _env_model()
    key = _cache_key(model, messages, schema)
    cached = _read_cached(key)
    if cached is not None:
        if VERBOSE:
            print("  cache hit", flush=True)
        return cached
    mode, _url = endpoint()
    body = _payload(mode, model, messages, schema, num_predict)
    raw = _post(body, timeout)
    try:
        parsed = parse_json_lenient(raw)
    except ValueError as exc:
        _write_cache(key, raw, None, str(exc))
        if VERBOSE:
            print(f"  json retry: {exc}", flush=True)
        retry_messages = [
            *messages,
            {"role": "assistant", "content": raw[:4000]},
            {
                "role": "user",
                "content": "The last reply was not valid JSON. Return one JSON object and nothing else.",
            },
        ]
        retry_key = _cache_key(model, retry_messages, schema)
        cached_retry = _read_cached(retry_key)
        if cached_retry is not None:
            return cached_retry
        retry_body = _payload(mode, model, retry_messages, schema, num_predict)
        raw_retry = _post(retry_body, timeout)
        try:
            parsed = parse_json_lenient(raw_retry)
        except ValueError as retry_exc:
            _write_cache(retry_key, raw_retry, None, str(retry_exc))
            raise
        _write_cache(retry_key, raw_retry, parsed, "")
        _write_cache(key, raw_retry, parsed, "")
        return parsed
    _write_cache(key, raw, parsed, "")
    return parsed


def slug_for(text: str) -> str:
    words = SLUG.sub(" ", normalize(text)).split()
    drop = {"name", "a", "an", "the"}
    kept = [word for word in words if word not in drop][:4]
    slug = "-".join(kept)[:28].strip("-")
    return slug or "prompt"


def content_words(text: str) -> list[str]:
    return [word for word in normalize(text).split() if word not in STOPWORDS]


def too_small(text: str) -> bool:
    """Closed sets of a handful of answers, such as the planets."""
    low = normalize(text)
    if any(phrase in low for phrase in TINY_PHRASES):
        return True
    words = content_words(text)
    return bool(words) and all(word in TINY_WORDS for word in words)


def overlaps(text: str, existing: list[set[str]]) -> bool:
    words = set(content_words(text))
    if not words:
        return True
    for other in existing:
        if not other:
            continue
        if words <= other or other <= words:
            return True
        if any(len(word) >= 5 and word in other for word in words):
            return True
    return False


_YEAR_NUM = re.compile(r"\b(?:1[89]\d{2}|20\d{2})\b")


def filter_ideas(ideas: list[dict], existing_texts: set[str], existing_sets: list[set[str]]) -> tuple[list[dict], Counter]:
    """Drop duplicates, tiny closed sets, and topics already in the bank."""
    reasons: Counter = Counter()
    kept: list[dict] = []
    sets = list(existing_sets)
    texts = set(existing_texts)
    for idea in ideas:
        if not isinstance(idea, dict):
            reasons["wording"] += 1
            continue
        text = str(idea.get("text") or "").strip()
        category = str(idea.get("category") or "general").strip()[:40] or "general"
        norm = normalize(text)
        if not text or not text.lower().startswith("name a") or " or " in text.lower() or "?" in text:
            reasons["wording"] += 1
            if VERBOSE:
                print(f"  reject wording: {text}", flush=True)
            continue
        if _YEAR_NUM.search(text):
            reasons["year"] += 1
            if VERBOSE:
                print(f"  reject year: {text}", flush=True)
            continue
        if norm in texts:
            reasons["duplicate"] += 1
            if VERBOSE:
                print(f"  reject duplicate: {text}", flush=True)
            continue
        if too_small(text):
            reasons["tiny"] += 1
            if VERBOSE:
                print(f"  reject tiny: {text}", flush=True)
            continue
        if overlaps(text, sets):
            reasons["overlap"] += 1
            if VERBOSE:
                print(f"  reject overlap: {text}", flush=True)
            continue
        kept.append({"text": text, "category": category})
        texts.add(norm)
        sets.append(set(content_words(text)))
    return kept, reasons


def familiarity_histogram(rows: list[dict]) -> str:
    counts = Counter(int(row.get("familiarity") or 0) for row in rows)
    return " ".join(f"{score}:{counts.get(score, 0)}" for score in range(1, 11))


def ping_model() -> int:
    mode, url = endpoint()
    print(f"llm {mode} {url} model {_env_model()}")
    try:
        data = chat_json(
            [
                {"role": "system", "content": "Reply with JSON only."},
                {"role": "user", "content": 'Return {"ok": true}.'},
            ],
            timeout=30,
        )
    except Exception as exc:
        print(f"ping failed: {exc}")
        return 1
    print(f"ping ok: {data}")
    return 0


def _existing_texts() -> set[str]:
    texts: set[str] = set()
    for prompt in list(load_published().values()) + list(_accepted_prompts()):
        texts.add(normalize(prompt.get("text") or ""))
    from pipeline.curated_loader import load_curated

    for prompt in load_curated():
        texts.add(normalize(prompt.get("text") or ""))
    return {text for text in texts if text}


def _existing_sets(texts: set[str]) -> list[set[str]]:
    return [set(content_words(text)) for text in texts]


def _accepted_prompts() -> list[dict]:
    if not ACCEPTED.exists():
        return []
    found = []
    for path in ACCEPTED.glob("*.json"):
        try:
            found.append(json.loads(path.read_text()))
        except json.JSONDecodeError:
            continue
    return found


def _row_from_model(row: dict, seen: set[str]) -> dict | None:
    name = str(row.get("name") or "").strip()
    norm = normalize(name)
    if not name or not norm or norm in seen or len(name) > 60 or is_profane(name):
        return None
    aliases = []
    for alias in row.get("aliases") or []:
        alias = str(alias).strip()
        if alias and normalize(alias) and normalize(alias) != norm and not is_profane(alias):
            aliases.append(alias)
    try:
        familiarity = int(round(float(row.get("familiarity"))))
    except (TypeError, ValueError):
        return None
    seen.add(norm)
    return {"name": name, "aliases": aliases[:4], "familiarity": max(1, min(10, familiarity))}


def _ask_answers(text: str) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for batch in range(3):
        avoid = ""
        if rows:
            sample = ", ".join(row["name"] for row in rows[-36:])
            avoid = f"\nDo not repeat any of these {len(rows)} answers, including: {sample}."
        messages = [
            {
                "role": "system",
                "content": "You list real answers for a category game. JSON only.",
            },
            {
                "role": "user",
                "content": (
                    f"Prompt: {text}\n"
                    "List 30 real, specific answers a person could give. Mix famous "
                    "and obscure. familiarity is an integer from 1 (specialists) to "
                    "10 (almost everyone). aliases are other real names, or empty. "
                    "No profanity."
                    f"{avoid}\n"
                    'Return {"answers": [{"name": "...", "aliases": [], "familiarity": 8}]}.'
                ),
            },
        ]
        data = chat_json(messages, schema=ANSWER_SCHEMA, num_predict=8192)
        added = 0
        for row in data.get("answers") or []:
            parsed = _row_from_model(row, seen)
            if parsed:
                rows.append(parsed)
                added += 1
        if VERBOSE:
            print(f"  batch {batch + 1}: +{added} (total {len(rows)})", flush=True)
        if added == 0:
            break
    return rows


def _verify(text: str, names: list[str]) -> set[str]:
    kept: set[str] = set()
    for start in range(0, len(names), 30):
        chunk = names[start : start + 30]
        messages = [
            {"role": "system", "content": "You check category membership. JSON only."},
            {
                "role": "user",
                "content": (
                    f"Prompt: {text}\n"
                    "Keep only names that are real, specific, correct answers. "
                    "Drop people, titles, or objects from the wrong category, and drop junk.\n"
                    + "\n".join(chunk)
                    + '\nReturn {"keep": ["name", ...]} using the names exactly.'
                ),
            },
        ]
        data = chat_json(messages, schema=KEEP_SCHEMA, timeout=180)
        kept.update(normalize(name) for name in (data.get("keep") or []) if normalize(str(name)))
    return kept


def _wiki_title(name: str) -> bool:
    """True when English Wikipedia has a page close to this name. Fail open on errors."""
    from urllib.parse import urlencode

    from pipeline.net import request_json

    query = urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": name,
            "srlimit": "1",
            "format": "json",
        }
    )
    try:
        data = request_json(
            f"https://en.wikipedia.org/w/api.php?{query}",
            bucket="wiki-title",
            gap_key="wiki",
            timeout=20,
        )
    except Exception:
        return True
    hits = ((data.get("query") or {}).get("search") or []) if isinstance(data, dict) else []
    return bool(hits)


def _zipf(name: str) -> float:
    if not zipf_frequency:
        return 0.0
    try:
        return float(zipf_frequency(name, "en"))
    except Exception:
        return 0.0


def _cross_check(rows: list[dict]) -> list[dict]:
    """Drop obscure answers Wikipedia has never heard of. Leave famous ones alone."""
    kept = []
    checked = 0
    for row in rows:
        if row["familiarity"] >= 7 or checked >= 30:
            kept.append(row)
            continue
        checked += 1
        if _wiki_title(row["name"]):
            kept.append(row)
    return kept


def _tier_rows(rows: list[dict]) -> list[dict] | None:
    """Percentile tiers. Flat familiarity scores still fill every tier when n is large."""
    if len(rows) < 6:
        return None
    prepared = []
    for row in rows:
        familiarity = int(row["familiarity"])
        prior = (familiarity - 1) / 9 * 4
        sitelinks = int(row.get("sitelinks") or 0)
        prepared.append(
            {
                "name": row["name"],
                "aliases": row["aliases"],
                "pop": popularity_score(sitelinks, _zipf(row["name"])) + prior,
                "sitelinks": sitelinks,
            }
        )
    return assign_by_popularity(prepared)


def _build(idea: dict, taken_ids: set[str]) -> dict | None:
    rows = _ask_answers(idea["text"])
    if len(rows) < 40:
        print(f"  skip few answers ({len(rows)}) familiarity [{familiarity_histogram(rows)}]")
        return None
    kept = _verify(idea["text"], [row["name"] for row in rows])
    if kept:
        rows = [row for row in rows if normalize(row["name"]) in kept]
    rows = _cross_check(rows)
    if len(rows) < 40:
        print(f"  skip verifier left {len(rows)} familiarity [{familiarity_histogram(rows)}]")
        return None
    tiered = _tier_rows(rows)
    if not tiered:
        print(f"  skip tier spread n={len(rows)} familiarity [{familiarity_histogram(rows)}]")
        return None
    slug = slug_for(idea["text"])
    prompt_id = f"llm-{slug}"
    suffix = 2
    while prompt_id in taken_ids:
        prompt_id = f"llm-{slug}-{suffix}"
        suffix += 1
    prompt = {
        "id": prompt_id,
        "text": idea["text"],
        "category": idea["category"],
        "source": "llm",
        "answers": tiered,
    }
    cleaned, errors = publishable(prompt)
    if errors:
        print(f"  skip {errors[0]} familiarity [{familiarity_histogram(rows)}]")
        return None
    return cleaned


def run_llm(count: int = 10, ping: bool = False, verbose: bool = False) -> int:
    global VERBOSE
    VERBOSE = verbose
    if ping:
        return ping_model()
    WORK.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    ACCEPTED.mkdir(parents=True, exist_ok=True)
    existing = _existing_texts()
    taken = {prompt["id"] for prompt in _accepted_prompts()} | set(load_published())
    made = 0
    attempts = 0
    while made < count and attempts < count * 3:
        need = max(4, count - made)
        try:
            ideas, reasons = filter_ideas(
                _raw_ideas(need, existing),
                existing,
                _existing_sets(existing),
            )
        except Exception as exc:
            print(f"ideas failed: {exc}")
            return 1 if made == 0 else 0
        print(
            "  ideas kept {kept} rejected {reasons}".format(
                kept=len(ideas),
                reasons=dict(reasons) or "{}",
            ),
            flush=True,
        )
        if not ideas:
            print("no new ideas")
            break
        for idea in ideas:
            if made >= count:
                break
            attempts += 1
            print(f"[llm {made}/{count}] {idea['text']}", flush=True)
            try:
                prompt = _build(idea, taken)
            except Exception as exc:
                print(f"  skip {type(exc).__name__}: {exc}")
                continue
            if not prompt:
                continue
            path = ACCEPTED / f"{prompt['id']}.json"
            path.write_text(json.dumps(prompt, ensure_ascii=False, indent=2) + "\n")
            (WORK / f"{prompt['id']}.json").write_text(path.read_text())
            taken.add(prompt["id"])
            existing.add(normalize(prompt["text"]))
            made += 1
            gem = next(answer["name"] for answer in prompt["answers"] if answer["gem"])
            counts = Counter(answer["tier"] for answer in prompt["answers"])
            print(f"  ok {prompt['id']} n={len(prompt['answers'])} gem={gem} {dict(counts)}", flush=True)
    print(f"llm prompts added: {made}")
    return 0 if made else 1


def _raw_ideas(count: int, existing: set[str]) -> list[dict]:
    sample = sorted(existing)[:80]
    messages = [
        {
            "role": "system",
            "content": (
                "You invent category prompts for a word game. "
                "Reply with a JSON object only. Disable extra commentary."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Give {count} original prompts. Each text must start with "
                "'Name a ' or 'Name an ', be under 90 characters, and name one clear "
                "category with hundreds of real answers. Skip closed sets under about "
                "30 members (planets, continents, days, months, state capitals). "
                "Vary the domains. Do not repeat a topic already listed. "
                "No years, no 'or', no question mark.\n"
                "Existing prompts:\n"
                + "\n".join(sample)
                + '\nReturn {"ideas": [{"text": "...", "category": "..."}]}.'
            ),
        },
    ]
    data = chat_json(messages, schema=IDEA_SCHEMA, num_predict=2048)
    ideas = data.get("ideas") or []
    return ideas if isinstance(ideas, list) else []
