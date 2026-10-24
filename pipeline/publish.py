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
from pipeline.audience import apply_audience, kept_prompt
from pipeline.cores import apply_known_cores
from pipeline.year_pin import year_pinned

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PROMPTS = DATA / "prompts"
ACCEPTED = CACHE / "accepted"
# A round fetches whole shard files. Keep each file small enough to stay quick on a phone.
MAX_SHARD_BYTES = 1_200_000
# Old category samples stopped around 70 answers. A sibling with hundreds means those are leftovers.
STALE_CAP = 75
EXHAUSTIVE_MARK = 200
CAPPED_PREFIXES = ("wd-film-", "wd-game-", "wd-album-", "wd-tvuk-", "wd-tv-", "wd-city-")
# A list under this size does not give rarity anything to do. Drop those only
# when the remaining bank is still well above the old 280-prompt catalog.
THIN_FLOOR = 80
THIN_KEEP_UNLESS = 300


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


def pack_shards(
    prompts: dict[str, dict],
    max_bytes: int = MAX_SHARD_BYTES,
    directory: str = "data/prompts",
) -> list[dict]:
    """Pack prompts into files of about `max_bytes`. One oversized prompt stays in its own file."""
    groups: list[list[str]] = []
    current: list[str] = []
    current_size = 2
    for prompt_id in sorted(prompts):
        encoded = json.dumps(prompts[prompt_id], ensure_ascii=False, indent=2).encode("utf-8")
        size = len(encoded) + 2
        if current and current_size + size > max_bytes:
            groups.append(current)
            current = []
            current_size = 2
        current.append(prompt_id)
        current_size += size
    if current:
        groups.append(current)
    return [{"file": f"{directory}/{index:04d}.json", "ids": ids} for index, ids in enumerate(groups, start=1)]


def prefer_answer_list(current: dict | None, incoming: dict) -> dict:
    """Keep the longer bank. A stale ~70-answer cache must not replace an exhaustive one."""
    if current is None:
        return incoming
    current_n = len(current.get("answers") or [])
    incoming_n = len(incoming.get("answers") or [])
    if incoming_n + 5 < current_n:
        print(
            f"keep {current['id']}: {current_n} answers beats cached {incoming_n}",
            flush=True,
        )
        return current
    return incoming


def _capped_kind(prompt_id: str) -> str | None:
    for prefix in CAPPED_PREFIXES:
        if prompt_id.startswith(prefix):
            return prefix
    return None


def drop_capped_samples(prompts: dict[str, dict], fresh_ids: set[str] | None = None) -> dict[str, dict]:
    """Drop leftover top-N samples once the same kind has a real exhaustive bank.

    A prompt rebuilt in this run is kept even when the real set is small
    (New York has 62 cities). Only an old sample that was not rebuilt is dropped.
    """
    fresh = fresh_ids or set()
    exhaustive = {
        _capped_kind(prompt["id"])
        for prompt in prompts.values()
        if _capped_kind(prompt["id"]) and len(prompt.get("answers") or []) >= EXHAUSTIVE_MARK
    }
    exhaustive.discard(None)
    if not exhaustive:
        return prompts
    kept: dict[str, dict] = {}
    for prompt_id, prompt in prompts.items():
        kind = _capped_kind(prompt_id)
        count = len(prompt.get("answers") or [])
        if kind in exhaustive and count <= STALE_CAP and prompt_id not in fresh:
            print(f"drop {prompt_id}: {count} answers still at the old cap", flush=True)
            continue
        kept[prompt_id] = prompt
    return kept


def apply_hand(merged: dict[str, dict], hand_prompts: list[dict]) -> dict[str, dict]:
    """Hand lists fill gaps. They do not shrink a harvested bank."""
    for prompt in hand_prompts:
        current = merged.get(prompt["id"])
        if current is None or len(prompt.get("answers") or []) > len(current.get("answers") or []):
            merged[prompt["id"]] = prompt
    return merged


def _keep(prompt: dict, label: str) -> dict | None:
    cleaned = scrub_prompt(prompt)
    errors = lint_prompt(cleaned)
    if errors:
        print(f"drop {label}: {errors[0]}", flush=True)
        return None
    return cleaned


def drop_rejected(prompts: dict[str, dict]) -> dict[str, dict]:
    """Drop year-pinned trivia, then thin lists when the fat bank can stand alone."""
    kept: dict[str, dict] = {}
    for prompt_id, prompt in prompts.items():
        if year_pinned(prompt):
            print(f"drop year-pinned {prompt_id}: {prompt.get('text')}", flush=True)
            continue
        kept[prompt_id] = prompt
    fat = {
        prompt_id: prompt
        for prompt_id, prompt in kept.items()
        if len(prompt.get("answers") or []) >= THIN_FLOOR
    }
    thin = [prompt_id for prompt_id in kept if prompt_id not in fat]
    if len(fat) >= THIN_KEEP_UNLESS:
        for prompt_id in thin:
            prompt = kept[prompt_id]
            if kept_prompt(prompt_id):
                fat[prompt_id] = prompt
                continue
            print(
                f"drop thin {prompt_id}: {len(prompt.get('answers') or [])} answers "
                f"({prompt.get('text')})",
                flush=True,
            )
        return fat
    if thin:
        print(
            f"keep {len(thin)} prompts under {THIN_FLOOR} answers; "
            f"only {len(fat)} have {THIN_FLOOR} or more",
            flush=True,
        )
    return kept


def assemble() -> tuple[dict, dict[str, dict]]:
    """Published bank, then cache when it is not a smaller stale copy, then larger hand lists."""
    old_index = load_index()
    merged = dict(load_published())
    for prompt_id, prompt in load_accepted().items():
        kept = _keep(prompt, prompt_id)
        if kept:
            merged[prompt_id] = prefer_answer_list(merged.get(prompt_id), kept)
    apply_hand(merged, load_curated())
    merged = drop_capped_samples(merged, set(load_accepted()))
    merged = apply_known_cores(merged)
    merged = drop_rejected(merged)
    merged = apply_audience(merged)
    return old_index, merged


def _points_at_live_shards(index: dict) -> bool:
    files = [str(shard.get("file") or "") for shard in index.get("shards") or []]
    return bool(files) and all(path.startswith("data/prompts/") for path in files)


def archive_legacy(old_index: dict) -> None:
    """Keep the pre-swap index so a browser that already loaded it can still score.

    Only the first move off data/prompts/ is archived. Later publishes must not
    overwrite that snapshot with the new deck.
    """
    legacy = DATA / "legacy" / "index.json"
    if legacy.exists() or not _points_at_live_shards(old_index):
        return
    _atomic(legacy, json.dumps(old_index, ensure_ascii=False, indent=2) + "\n")
    print(f"archived legacy index ({old_index.get('promptCount')} prompts)", flush=True)


def write_bank(old_index: dict, prompts: dict[str, dict]) -> dict:
    # Snapshot the shards a live session is already fetching before replacing the index.
    archive_legacy(old_index)
    digest = content_hash(prompts)
    version = int(old_index.get("version") or 0)
    if digest != old_index.get("hash"):
        version += 1
    # New shards live beside the old ones. data/prompts/ stays byte-stable.
    directory = f"data/bank/v{version}"
    if directory.startswith("data/prompts"):
        raise RuntimeError("refusing to overwrite the shards a live game is fetching")
    groups = pack_shards(prompts, directory=directory)
    shard_root = ROOT / directory
    shard_root.mkdir(parents=True, exist_ok=True)
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
    for path in shard_root.glob("*.json"):
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
