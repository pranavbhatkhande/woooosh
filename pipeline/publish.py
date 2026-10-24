"""Merge the hand bank, cached generations, and curated prompts into shards."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pipeline.curated_loader import load_curated
from pipeline.net import CACHE
from pipeline.quality import lint_prompt
from pipeline.scrub import scrub_prompt

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROMPTS = DATA / "prompts"
ACCEPTED = CACHE / "accepted"
SHARD_SIZE = 45


def _read_json(path: Path):
    return json.loads(path.read_text())


def load_index() -> dict:
    path = DATA / "index.json"
    if not path.exists():
        return {}
    return _read_json(path)


def load_published() -> dict[str, dict]:
    index = load_index()
    prompts: dict[str, dict] = {}
    for shard in index.get("shards") or []:
        path = ROOT / shard["file"]
        if not path.exists():
            continue
        for prompt in _read_json(path):
            prompts[prompt["id"]] = prompt
    return prompts


def load_accepted() -> dict[str, dict]:
    found: dict[str, dict] = {}
    if not ACCEPTED.exists():
        return found
    for path in sorted(ACCEPTED.glob("*.json")):
        prompt = _read_json(path)
        if prompt.get("id"):
            found[prompt["id"]] = prompt
    return found


def content_hash(prompts: dict[str, dict]) -> str:
    ordered = [prompts[key] for key in sorted(prompts)]
    blob = json.dumps(ordered, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def assign_shards(old_index: dict, ids: set[str]) -> list[dict]:
    """Keep each id in its current shard. New ids fill the last shard, then a new file."""
    groups: list[dict] = []
    placed: set[str] = set()
    for shard in old_index.get("shards") or []:
        kept = [prompt_id for prompt_id in shard.get("ids") or [] if prompt_id in ids]
        placed.update(kept)
        groups.append({"file": shard["file"], "ids": kept})
    fresh = sorted(prompt_id for prompt_id in ids if prompt_id not in placed)
    used = {group["file"] for group in groups}

    def fresh_file() -> str:
        number = 1
        while True:
            rel = f"data/prompts/{number:04d}.json"
            if rel not in used:
                used.add(rel)
                return rel
            number += 1

    for prompt_id in fresh:
        if not groups or len(groups[-1]["ids"]) >= SHARD_SIZE:
            groups.append({"file": fresh_file(), "ids": []})
        groups[-1]["ids"].append(prompt_id)
    return [group for group in groups if group["ids"]]


def _keep(prompt: dict, label: str) -> dict | None:
    cleaned = scrub_prompt(prompt)
    errors = lint_prompt(cleaned)
    if errors:
        print(f"drop {label}: {errors[0]}", flush=True)
        return None
    return cleaned


def assemble() -> tuple[dict, dict[str, dict]]:
    """Published bank, then cache (scrubbed), then curated. Curated always wins."""
    old_index = load_index()
    merged = dict(load_published())
    for prompt_id, prompt in load_accepted().items():
        kept = _keep(prompt, prompt_id)
        if kept:
            merged[prompt_id] = kept
    for prompt in load_curated():
        merged[prompt["id"]] = prompt
    return old_index, merged


def write_bank(old_index: dict, prompts: dict[str, dict]) -> dict:
    digest = content_hash(prompts)
    version = int(old_index.get("version") or 0)
    if digest != old_index.get("hash"):
        version += 1
    groups = assign_shards(old_index, set(prompts))
    PROMPTS.mkdir(parents=True, exist_ok=True)
    used: set[str] = set()
    shards = []
    for group in groups:
        rel = group["file"]
        used.add(rel)
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = [prompts[prompt_id] for prompt_id in group["ids"]]
        _atomic(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        shards.append({"file": rel, "count": len(group["ids"]), "ids": group["ids"]})
    if PROMPTS.exists():
        for path in PROMPTS.glob("*.json"):
            rel = path.relative_to(ROOT).as_posix()
            if rel not in used:
                path.unlink()
    answer_count = sum(len(prompts[prompt_id]["answers"]) for prompt_id in prompts)
    index = {
        "version": version,
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "promptCount": len(prompts),
        "answerCount": answer_count,
        "hash": digest,
        "shards": shards,
    }
    _atomic(DATA / "index.json", json.dumps(index, ensure_ascii=False, indent=2) + "\n")
    print(f"published {len(prompts)} prompts, {answer_count} answers, version {version}", flush=True)
    return index


def _atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    tmp.replace(path)


def publish() -> dict:
    old_index, prompts = assemble()
    return write_bank(old_index, prompts)


def check_bank() -> int:
    index_path = DATA / "index.json"
    if not index_path.exists():
        print("no data/index.json")
        return 1
    index = _read_json(index_path)
    problems = 0
    seen: set[str] = set()
    answer_count = 0
    for shard in index.get("shards") or []:
        path = ROOT / shard["file"]
        if not path.exists():
            print(f"missing {shard['file']}")
            problems += 1
            continue
        prompts = _read_json(path)
        ids = [prompt["id"] for prompt in prompts]
        if len(prompts) != shard.get("count") or ids != shard.get("ids"):
            print(f"{shard['file']} does not match the index")
            problems += 1
        for prompt in prompts:
            if prompt["id"] in seen:
                print(f"duplicate id {prompt['id']}")
                problems += 1
            seen.add(prompt["id"])
            answer_count += len(prompt.get("answers") or [])
            errors = lint_prompt(prompt)
            for error in errors:
                print(f"{prompt['id']}: {error}")
                problems += 1
    if len(seen) != index.get("promptCount"):
        print("promptCount does not match the shards")
        problems += 1
    if answer_count != index.get("answerCount"):
        print("answerCount does not match the shards")
        problems += 1
    if problems == 0:
        loaded = {}
        for shard in index.get("shards") or []:
            for prompt in _read_json(ROOT / shard["file"]):
                loaded[prompt["id"]] = prompt
        if content_hash(loaded) != index.get("hash"):
            print("hash does not match the shards")
            problems += 1
    sources: dict[str, int] = {}
    for shard in index.get("shards") or []:
        for prompt in _read_json(ROOT / shard["file"]):
            sources[prompt.get("source") or "?"] = sources.get(prompt.get("source") or "?", 0) + 1
    print(f"checked {len(seen)} prompts, problems {problems}, sources {sources}")
    return 1 if problems else 0
