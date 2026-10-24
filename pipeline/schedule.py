"""Pinned daily prompts. Existing dates stay put when the bank grows."""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone


def pick_ids(ids: list[str], day: str, count: int = 7) -> list[str]:
    pool = sorted(set(ids))
    rng = random.Random(f"woooosh-daily-v1|{day}")
    rng.shuffle(pool)
    return pool[:count]


def extend_schedule(existing: dict | None, ids: list[str], today: str, days: int = 450, keep_past: int = 14) -> dict[str, list[str]]:
    known = set(ids)
    start = date.fromisoformat(today)
    keep_from = start - timedelta(days=keep_past)
    horizon = start + timedelta(days=days - 1)
    kept: dict[str, list[str]] = {}
    for key, value in (existing or {}).items():
        try:
            stamp = date.fromisoformat(key)
        except ValueError:
            continue
        if stamp < keep_from or stamp > horizon:
            continue
        if _valid(value, known):
            kept[key] = list(value)
        elif stamp >= start:
            kept[key] = pick_ids(ids, key)
    cursor = start - timedelta(days=1)
    while cursor <= horizon:
        key = cursor.isoformat()
        if key not in kept:
            kept[key] = pick_ids(ids, key)
        cursor += timedelta(days=1)
    return dict(sorted(kept.items()))


def today_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _valid(value, known: set[str]) -> bool:
    return isinstance(value, list) and len(value) == 7 and len(set(value)) == 7 and all(item in known for item in value)
