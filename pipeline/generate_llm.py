"""Qwen-curated prompts. Resumable: each model call is cached, finished prompts are skipped."""

from __future__ import annotations

import hashlib
import json
import re

import requests

from pipeline.http_client import USER_AGENT, PoliteHttp
from pipeline.llm_client import LlmClient, LlmError
from pipeline.naming import acceptable_label, present_name
from pipeline.normalize import normalize
from pipeline.paths import OUT_DIR, OUT_PROMPTS
from pipeline.publish import load_data_prompts, load_out_prompts
from pipeline.quality import evaluate, repair_answers
from pipeline.tiering import assign_tiers, familiarity_score
from pipeline.curated import load_curated

SYSTEM = (
    "You edit WOOOOSH, a family-friendly party game. Players type one answer to an open prompt. "
    "Reply with one JSON object only. No markdown, no commentary."
)
STOP = {"name", "a", "an", "the", "of", "that", "you", "your", "people", "something", "someone", "thing"}


def generate_llm(count: int = 25, url: str = "http://localhost:11434/v1", model: str = "qwen3.8:27b", timeout: int = 180, refresh: bool = False) -> int:
    if count < 1:
        print("Nothing to do.")
        return 0
    client = LlmClient(url, model, timeout=timeout)
    OUT_PROMPTS.mkdir(parents=True, exist_ok=True)
    existing = _existing_texts()
    print(f"LLM {model} at {url}. Want {count} new prompts. Avoiding {len(existing)} existing.", flush=True)
    accepted = 0
    attempts = 0
    limit = max(count * 4, 8)
    while accepted < count and attempts < limit:
        try:
            ideas = _ideas(client, existing, min(10, (count - accepted) * 2))
        except LlmError as exc:
            print(f"LLM error: {exc}", flush=True)
            return 1 if accepted == 0 else 0
        if not ideas:
            print("Model returned no new ideas.", flush=True)
            break
        for idea in ideas:
            if accepted >= count or attempts >= limit:
                break
            attempts += 1
            text = _clean_text(idea.get("text", ""))
            if not text or _too_close(text, existing):
                continue
            prompt_id = _prompt_id(text)
            path = OUT_PROMPTS / f"{prompt_id}.json"
            rejected = OUT_DIR / "llm-rejected" / f"{prompt_id}.json"
            if path.exists() and not refresh:
                accepted += 1
                existing.append(text)
                continue
            if rejected.exists() and not refresh:
                continue
            print(f"Building {prompt_id}: {text}", flush=True)
            try:
                prompt, issues = _build(client, prompt_id, text, idea.get("category") or "everyday")
            except LlmError as exc:
                print(f"  error: {exc}", flush=True)
                return 1 if accepted == 0 else 0
            if prompt is None:
                rejected.parent.mkdir(parents=True, exist_ok=True)
                rejected.write_text(json.dumps({"text": text, "issues": issues}, indent=2) + "\n", encoding="utf-8")
                print(f"  reject: {', '.join(issues)}", flush=True)
                continue
            path.write_text(json.dumps(prompt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            existing.append(text)
            accepted += 1
            gem = next(answer["name"] for answer in prompt["answers"] if answer["gem"])
            print(f"  OK answers={len(prompt['answers'])} gem={gem}", flush=True)
    print(f"Accepted {accepted} of {count} requested.", flush=True)
    return 0 if accepted else 1


def _build(client: LlmClient, prompt_id: str, text: str, category: str):
    gate = client.json_chat(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                "Is this prompt fair for a party game where any answer on a hidden list should be defensible?\n"
                f"Prompt: {text}\n"
                'Reply {"ambiguous": false, "kind": "subjective", "note": "short"}. '
                "ambiguous is true for opinions (best, favorite), one-right-answer trivia, or unclear boundaries. "
                "kind is factual when answers are checkable entities, otherwise subjective."
            )},
        ],
        temperature=0.1,
        max_tokens=300,
        purpose="gate",
    )
    if bool(gate.get("ambiguous")):
        return None, [f"ambiguous:{gate.get('note', '')[:80]}"]
    kind = "factual" if gate.get("kind") == "factual" else "subjective"
    raw = []
    for round_index in range(4):
        if len(raw) >= 70:
            break
        batch = client.json_chat(
            [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": _answer_prompt(text, raw)},
            ],
            temperature=0.5,
            max_tokens=3500,
            purpose=f"answers-{round_index}",
        )
        raw = _merge_answers(raw, batch.get("answers") or [])
    if len(raw) < 40:
        return None, [f"too-few-raw:{len(raw)}"]
    kept = _verify(client, text, raw)
    if kind == "factual":
        ratio = _wiki_ratio([row["name"] for row in kept])
        if ratio < 0.45:
            return None, [f"wiki-unconfirmed:{ratio:.2f}"]
    if len(kept) < 40:
        return None, [f"too-few-verified:{len(kept)}"]
    for row in kept:
        row["popularity"] = familiarity_score(int(row.get("familiarity") or 3), zipf=_safe_zipf(row["name"]))
    repaired = repair_answers(kept)
    if len(repaired) < 40:
        return None, [f"too-few-after-repair:{len(repaired)}"]
    assign_tiers(repaired)
    prompt = {
        "id": prompt_id,
        "text": text,
        "category": _slug(category) or "everyday",
        "source": "llm",
        "answers": [
            {"name": row["name"], "aliases": list(row.get("aliases") or []), "tier": row["tier"], "gem": bool(row.get("gem"))}
            for row in repaired
        ],
    }
    issues = evaluate(prompt)
    if issues:
        return None, issues
    return prompt, []


def _answer_prompt(text: str, existing: list[dict]) -> str:
    have = ", ".join(row["name"] for row in existing[:80])
    return (
        f"Prompt: {text}\n"
        "Return 28 more acceptable answers a player could fairly give. Mix obvious and uncommon ones.\n"
        "familiarity is 1 (almost everyone) through 6 (true but rarely the first thought).\n"
        "Mark showoff true for at most 6 cliché clever answers that sound rare and are not.\n"
        f"Do not repeat: {have or '(none yet)'}\n"
        'JSON: {"answers":[{"name":"short name","aliases":["alt"],"familiarity":3,"showoff":false}]}'
    )


def _verify(client: LlmClient, text: str, rows: list[dict]) -> list[dict]:
    kept = []
    for start in range(0, len(rows), 18):
        chunk = rows[start : start + 18]
        payload = client.json_chat(
            [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": (
                    f"Prompt: {text}\n"
                    "For each answer, verdict keep only if a fair player would accept it. "
                    "Drop jokes, duplicates, wrong-category items, and anything offensive.\n"
                    + json.dumps([row["name"] for row in chunk])
                    + '\nJSON: {"results":[{"name":"...","verdict":"keep"}]}'
                )},
            ],
            temperature=0.1,
            max_tokens=2000,
            purpose="verify",
        )
        verdicts = {}
        for result in payload.get("results") or []:
            verdicts[normalize(str(result.get("name", "")))] = str(result.get("verdict", "")).lower()
        for row in chunk:
            verdict = verdicts.get(normalize(row["name"]), "keep")
            if verdict != "drop":
                kept.append(row)
    return kept


def _ideas(client: LlmClient, existing: list[str], need: int) -> list[dict]:
    avoid = "\n".join(existing[:300])
    payload = client.json_chat(
        [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"Propose {need} new prompts. Each text starts with 'Name'. "
                "A typical adult could offer 40 or more real answers. No single correct answer. "
                "No sexual, hateful, or gory prompts. Vary everyday life, food, work, weather, travel, and culture. "
                "Do not paraphrase the avoid list.\n"
                f"Avoid:\n{avoid}\n"
                'JSON: {"ideas":[{"text":"Name a reason a picnic gets rained out","category":"everyday","kind":"subjective"}]}'
            )},
        ],
        temperature=0.7,
        max_tokens=2000,
        purpose="ideas",
    )
    ideas = []
    for idea in payload.get("ideas") or []:
        if isinstance(idea, dict) and idea.get("text"):
            ideas.append(idea)
    return ideas


def _merge_answers(existing: list[dict], incoming: list) -> list[dict]:
    by_key = {normalize(row["name"]): row for row in existing}
    for item in incoming:
        if not isinstance(item, dict):
            continue
        name = present_name(str(item.get("name") or ""))
        if not acceptable_label(name):
            continue
        key = normalize(name)
        if not key or key in by_key:
            continue
        aliases = []
        for alias in item.get("aliases") or []:
            presented = present_name(str(alias))
            if acceptable_label(presented) and normalize(presented) not in {key, normalize(name)}:
                aliases.append(presented)
        try:
            familiarity = int(item.get("familiarity") or 3)
        except (TypeError, ValueError):
            familiarity = 3
        by_key[key] = {
            "name": name,
            "aliases": aliases[:5],
            "familiarity": min(6, max(1, familiarity)),
            "showoff": bool(item.get("showoff")),
        }
    return list(by_key.values())


def _wiki_ratio(names: list[str]) -> float:
    if not names:
        return 0.0
    http = PoliteHttp(delay=1.0)
    hits = 0
    checked = 0
    for start in range(0, len(names), 40):
        chunk = names[start : start + 40]
        http.wait()
        try:
            response = http.session.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action": "query", "format": "json", "redirects": 1, "titles": "|".join(chunk)},
                headers={"User-Agent": USER_AGENT},
                timeout=(8, 30),
            )
            pages = response.json().get("query", {}).get("pages", {})
        except (requests.RequestException, ValueError):
            continue
        for page in pages.values():
            checked += 1
            if not page.get("missing"):
                hits += 1
    if checked == 0:
        return 0.0
    return hits / len(names)


def _existing_texts() -> list[str]:
    texts = []
    for prompt in load_out_prompts() + load_data_prompts() + load_curated():
        if prompt.get("text"):
            texts.append(prompt["text"])
    return texts


def _too_close(text: str, existing: list[str]) -> bool:
    left = _tokens(text)
    if not left:
        return True
    for other in existing:
        right = _tokens(other)
        if not right:
            continue
        if len(left & right) / len(left | right) >= 0.62:
            return True
    return False


def _tokens(text: str) -> set[str]:
    return {token for token in normalize(text).split() if token not in STOP and len(token) > 2}


def _clean_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip().rstrip("?").strip()
    if len(cleaned) < 12 or len(cleaned) > 90:
        return ""
    if not cleaned.lower().startswith("name "):
        return ""
    return cleaned[:1].upper() + cleaned[1:]


def _prompt_id(text: str) -> str:
    digest = hashlib.sha1(normalize(text).encode("utf-8")).hexdigest()[:6]
    words = [word for word in re.findall(r"[a-z0-9]+", normalize(text)) if word not in STOP][:4]
    slug = "-".join(words) or "prompt"
    return f"llm-{slug}-{digest}"


def _slug(value: str) -> str:
    return "-".join(re.findall(r"[a-z0-9]+", value.lower())[:3])


def _safe_zipf(label: str) -> float:
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        return 0.0
    if len(label) < 4:
        return 0.0
    return float(zipf_frequency(label.lower(), "en"))
