"""Merge sources into static shards the site can lazy-load."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from pipeline.curated import load_curated
from pipeline.paths import DATA_DIR, OUT_PROMPTS, PROMPT_DIR
from pipeline.quality import evaluate
from pipeline.schedule import extend_schedule, today_iso
from pipeline.tiering import TIER_ORDER, TRAP_TIER

SHARD_SIZE = 20


def publish(days: int = 450) -> int:
    prompts, problems = collect()
    if problems:
        for prompt_id, issues in problems:
            print(f"drop {prompt_id}: {', '.join(issues)}")
    if len(prompts) < 40:
        print(f"Only {len(prompts)} prompts passed the gates.")
        return 1
    schedule = extend_schedule(_read_schedule(), [prompt["id"] for prompt in prompts], today_iso(), days=days)
    digest = _digest(prompts)
    previous = _read_index()
    unchanged = previous.get("contentHash") == digest and _read_schedule() == schedule
    if unchanged:
        print(f"No changes. bank v{previous.get('version')} · {len(prompts)} prompts")
        return 0
    version = int(previous.get("version") or 0) + 1
    _write(prompts, schedule, digest, version)
    print(f"Published bank v{version} · {len(prompts)} prompts · {len(schedule)} daily dates")
    return 0


def validate() -> int:
    prompts, problems = collect()
    print(f"{len(prompts)} prompts pass. {len(problems)} dropped.")
    for prompt_id, issues in problems[:30]:
        print(f"  {prompt_id}: {', '.join(issues)}")
    return 0 if prompts else 1


def collect() -> tuple[list[dict], list[tuple[str, list[str]]]]:
    merged = merge_prompts(load_data_prompts(), load_out_prompts(), load_curated())
    good = []
    problems = []
    seen_text = set()
    for prompt in merged:
        issues = evaluate(prompt)
        folded = " ".join((prompt.get("text") or "").lower().split())
        if folded in seen_text:
            issues.append("duplicate-text")
        if issues:
            problems.append((prompt.get("id", "?"), issues))
            continue
        seen_text.add(folded)
        good.append(prompt)
    return good, problems


def merge_prompts(*groups: list[dict]) -> list[dict]:
    by_id = {}
    for group in groups:
        for prompt in group:
            if prompt.get("id"):
                by_id[prompt["id"]] = prompt
    return [by_id[key] for key in sorted(by_id)]


def shard_prompts(prompts: list[dict], size: int = SHARD_SIZE) -> list[list[dict]]:
    return [prompts[index : index + size] for index in range(0, len(prompts), size)] or [[]]


def load_out_prompts() -> list[dict]:
    if not OUT_PROMPTS.exists():
        return []
    prompts = []
    for path in sorted(OUT_PROMPTS.glob("*.json")):
        prompts.append(json.loads(path.read_text(encoding="utf-8")))
    return prompts


def load_data_prompts() -> list[dict]:
    index_path = DATA_DIR / "index.json"
    if not index_path.exists():
        return []
    index = json.loads(index_path.read_text(encoding="utf-8"))
    prompts = []
    for shard in index.get("shards") or []:
        path = DATA_DIR / shard["file"]
        if path.exists():
            prompts.extend(json.loads(path.read_text(encoding="utf-8")).get("prompts") or [])
    return prompts


def _write(prompts: list[dict], schedule: dict, digest: str, version: int) -> None:
    if PROMPT_DIR.exists():
        for stale in PROMPT_DIR.glob("*.json"):
            stale.unlink()
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    shards = shard_prompts(prompts, SHARD_SIZE)
    shard_meta = []
    for number, chunk in enumerate(shards, start=1):
        name = f"prompts/{number:04d}.json"
        (DATA_DIR / name).parent.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / name).write_text(json.dumps({"prompts": chunk}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        shard_meta.append({"file": name, "count": len(chunk), "ids": [prompt["id"] for prompt in chunk]})
    by_source = {}
    for prompt in prompts:
        by_source[prompt.get("source") or "unknown"] = by_source.get(prompt.get("source") or "unknown", 0) + 1
    index = {
        "version": version,
        "contentHash": digest,
        "promptCount": len(prompts),
        "shardSize": SHARD_SIZE,
        "generated": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "bySource": by_source,
        "tiers": [
            {"id": tier, "points": points, "trap": tier == TRAP_TIER}
            for tier, points, _cut in TIER_ORDER
        ],
        "shards": shard_meta,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    daily = {"version": version, "dates": schedule}
    (DATA_DIR / "daily.json").write_text(json.dumps(daily, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _digest(prompts: list[dict]) -> str:
    blob = json.dumps(prompts, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _read_index() -> dict:
    path = DATA_DIR / "index.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _read_schedule() -> dict:
    path = DATA_DIR / "daily.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("dates") or {}
