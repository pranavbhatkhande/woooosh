"""Curate prompts with a local Ollama or OpenAI-compatible model.

The seed bank does not depend on this. It is for the owner's machine, where
Ollama serves qwen3.8:27b. Runs are resumable: finished prompts are skipped.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

from pipeline.net import CACHE
from pipeline.normalize import normalize
from pipeline.profanity import is_profane
from pipeline.publish import load_published
from pipeline.quality import publishable
from pipeline.tiers import tier_for_familiarity

ROOT = Path(__file__).resolve().parents[1]
WORK = CACHE / "llm"
ACCEPTED = CACHE / "accepted"
DEFAULT_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3.8:27b"
SLUG = re.compile(r"[^a-z0-9]+")


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


def _payload(mode: str, model: str, messages: list[dict]) -> dict:
    if mode == "ollama":
        return {
            "model": model,
            "messages": messages,
            "stream": False,
            "think": False,
            "format": "json",
            "options": {"temperature": 0.4, "num_predict": 4096},
        }
    return {
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 4096,
        "think": False,
        "response_format": {"type": "json_object"},
    }


def chat_json(messages: list[dict], *, timeout: int = 180) -> dict:
    mode, url = endpoint()
    body = json.dumps(_payload(mode, _env_model(), messages)).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("PIPELINE_LLM_TOKEN") or ""
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        if "think" in detail.lower():
            return _chat_without_think(messages, timeout)
        raise RuntimeError(f"llm http {exc.code}: {detail}") from exc
    text = _message_text(payload)
    return _parse_json(text)


def _chat_without_think(messages: list[dict], timeout: int) -> dict:
    mode, url = endpoint()
    body_obj = _payload(mode, _env_model(), messages)
    body_obj.pop("think", None)
    body = json.dumps(body_obj).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    token = os.environ.get("PIPELINE_LLM_TOKEN") or ""
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return _parse_json(_message_text(payload))


def _message_text(payload: dict) -> str:
    if isinstance(payload.get("message"), dict):
        return str(payload["message"].get("content") or "")
    choices = payload.get("choices") or []
    if choices:
        return str((choices[0].get("message") or {}).get("content") or "")
    return ""


def _parse_json(text: str) -> dict:
    raw = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fenced:
        raw = fenced.group(1).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise RuntimeError("model did not return a JSON object")
    data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise RuntimeError("model JSON was not an object")
    return data


def slug_for(text: str) -> str:
    words = SLUG.sub(" ", normalize(text)).split()
    drop = {"name", "a", "an", "the"}
    kept = [word for word in words if word not in drop][:4]
    slug = "-".join(kept)[:28].strip("-")
    return slug or "prompt"


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


def _ask_ideas(count: int, existing: set[str]) -> list[dict]:
    sample = sorted(existing)[:40]
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
                "'Name a ' or 'Name an ', be under 90 characters, name one clear "
                "category, and have at least 50 real answers. No years, no 'or', "
                "no question mark. Avoid these existing prompts:\n"
                + "\n".join(sample)
                + '\nReturn {"ideas": [{"text": "...", "category": "..."}]}.'
            ),
        },
    ]
    data = chat_json(messages)
    ideas = data.get("ideas") or []
    cleaned = []
    for idea in ideas:
        text = str(idea.get("text") or "").strip()
        category = str(idea.get("category") or "general").strip()[:40]
        if not text or normalize(text) in existing:
            continue
        if " or " in text.lower() or "?" in text:
            continue
        if not text.lower().startswith("name a"):
            continue
        cleaned.append({"text": text, "category": category or "general"})
    return cleaned


def _ask_answers(text: str) -> list[dict]:
    messages = [
        {
            "role": "system",
            "content": "You list real answers for a category game. JSON only.",
        },
        {
            "role": "user",
            "content": (
                f'Prompt: {text}\n'
                "List 60 real, specific answers a person could give. Mix famous "
                "and obscure. familiarity is an integer from 1 (specialists) to "
                "10 (almost everyone). aliases are other real names, or empty. "
                'No profanity. Return {"answers": [{"name": "...", "aliases": [], "familiarity": 8}]}.'
            ),
        },
    ]
    data = chat_json(messages)
    rows = []
    seen: set[str] = set()
    for row in data.get("answers") or []:
        name = str(row.get("name") or "").strip()
        norm = normalize(name)
        if not name or not norm or norm in seen or len(name) > 60 or is_profane(name):
            continue
        aliases = []
        for alias in row.get("aliases") or []:
            alias = str(alias).strip()
            if alias and normalize(alias) and normalize(alias) != norm and not is_profane(alias):
                aliases.append(alias)
        try:
            familiarity = int(round(float(row.get("familiarity"))))
        except (TypeError, ValueError):
            continue
        seen.add(norm)
        rows.append({"name": name, "aliases": aliases[:4], "familiarity": max(1, min(10, familiarity))})
    return rows


def _verify(text: str, names: list[str]) -> set[str]:
    messages = [
        {"role": "system", "content": "You check category membership. JSON only."},
        {
            "role": "user",
            "content": (
                f"Prompt: {text}\n"
                "Keep only names that are real, specific, correct answers. "
                "Drop people, titles, or objects from the wrong category, and drop junk.\n"
                + "\n".join(names)
                + '\nReturn {"keep": ["name", ...]} using the names exactly.'
            ),
        },
    ]
    data = chat_json(messages, timeout=180)
    return {normalize(name) for name in (data.get("keep") or []) if normalize(str(name))}


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
    """Map familiarity onto tiers and force one non-famous gem. None if a tier is empty."""
    from collections import Counter

    ranked = sorted(rows, key=lambda row: (-row["familiarity"], row["name"].lower()))
    answers = []
    for row in ranked:
        answers.append(
            {
                "name": row["name"],
                "aliases": row["aliases"],
                "tier": tier_for_familiarity(row["familiarity"]),
                "gem": False,
                "pop": row["familiarity"],
            }
        )
    present = {answer["tier"] for answer in answers}
    if not {"taxi", "climb", "burn", "stall", "apogee"} <= present:
        return None
    counts = Counter(answer["tier"] for answer in answers)
    rare = [answer for answer in answers if answer["pop"] <= 3 and counts[answer["tier"]] > 1]
    if not rare:
        return None
    gem = sorted(rare, key=lambda answer: (abs(answer["pop"] - 2), answer["name"].lower()))[0]
    for answer in answers:
        if answer is gem:
            answer["tier"] = "escape"
            answer["gem"] = True
    return answers


def _build(idea: dict, taken_ids: set[str]) -> dict | None:
    rows = _ask_answers(idea["text"])
    if len(rows) < 40:
        print(f"  skip few answers ({len(rows)})")
        return None
    kept = _verify(idea["text"], [row["name"] for row in rows])
    if kept:
        rows = [row for row in rows if normalize(row["name"]) in kept]
    rows = _cross_check(rows)
    if len(rows) < 40:
        print(f"  skip verifier left {len(rows)}")
        return None
    tiered = _tier_rows(rows)
    if not tiered:
        print("  skip tier spread")
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
        print(f"  skip {errors[0]}")
        return None
    return cleaned


def run_llm(count: int = 10, ping: bool = False) -> int:
    if ping:
        return ping_model()
    WORK.mkdir(parents=True, exist_ok=True)
    ACCEPTED.mkdir(parents=True, exist_ok=True)
    existing = _existing_texts()
    taken = {prompt["id"] for prompt in _accepted_prompts()} | set(load_published())
    made = 0
    attempts = 0
    while made < count and attempts < count * 3:
        need = max(4, count - made)
        try:
            ideas = _ask_ideas(need, existing)
        except Exception as exc:
            print(f"ideas failed: {exc}")
            return 1 if made == 0 else 0
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
            print(f"  ok {prompt['id']} n={len(prompt['answers'])} gem={gem}", flush=True)
    print(f"llm prompts added: {made}")
    return 0 if made else 1
