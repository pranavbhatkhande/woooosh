"""Fold accepted AI-judge answers into published prompts without retiering."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.normalize import keys_for, normalize
from pipeline.profanity import is_profane
from pipeline.publish import load_index, load_published, write_bank
from pipeline.tiers import TIER_ORDER

PLAYABLE = ("taxi", "climb", "burn", "stall", "apogee")
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FILE = ROOT / "pipeline" / "cache" / "judged.json"


def fold_answer(prompt: dict, record: dict) -> str:
    """Append one judged answer. Returns added, skipped, or rejected.

    Existing tiers stay put. A judged answer is never the gem.
    """
    canonical = (record.get("canonical") or record.get("answer") or "").strip()
    if not canonical or len(canonical) > 60 or is_profane(canonical):
        return "rejected"
    tier = (record.get("tier") or "").strip()
    if tier == "escape":
        tier = "apogee"
    if tier not in PLAYABLE:
        return "rejected"
    norm = normalize(canonical)
    if not norm:
        return "rejected"
    claimed: set[str] = set()
    for answer in prompt.get("answers") or []:
        claimed |= keys_for(answer.get("name") or "", answer.get("aliases") or [])
    if norm in claimed:
        return "skipped"
    prompt["answers"].append({"name": canonical, "aliases": [], "tier": tier, "gem": False})
    rank = {name: index for index, name in enumerate(TIER_ORDER)}
    prompt["answers"].sort(key=lambda answer: rank.get(answer.get("tier"), 99))
    return "added"


def import_judged(path: str | None = None) -> int:
    source = Path(path) if path else DEFAULT_FILE
    if not source.exists():
        print(f"no judged export at {source}")
        print("pull one with: node deploy/pull-judged.mjs")
        return 1
    records = json.loads(source.read_text())
    if isinstance(records, dict):
        records = records.get("answers") or records.get("items") or []
    if not isinstance(records, list):
        print("judged file must be a list")
        return 1
    prompts = load_published()
    if not prompts:
        print("publish a bank before importing judged answers")
        return 1
    added = skipped = rejected = missing = 0
    for record in records:
        prompt = prompts.get((record or {}).get("promptId") or "")
        if prompt is None:
            missing += 1
            continue
        result = fold_answer(prompt, record)
        if result == "added":
            added += 1
        elif result == "skipped":
            skipped += 1
        else:
            rejected += 1
    if added:
        write_bank(load_index(), prompts)
    print(f"judged import added {added}, skipped {skipped}, rejected {rejected}, unknown prompt {missing}")
    return 0
