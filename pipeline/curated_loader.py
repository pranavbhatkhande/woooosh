"""Hand-authored prompts. Answer lines are most-familiar first. Aliases follow a pipe."""

from __future__ import annotations

from pipeline.curated_sets import SETS
from pipeline.quality import publishable
from pipeline.tiers import assign_ordered


def _entries(block: str) -> list[dict]:
    entries = []
    for raw in block.strip().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = [part.strip() for part in line.split("|") if part.strip()]
        entries.append({"name": parts[0], "aliases": parts[1:]})
    return entries


def load_curated() -> list[dict]:
    prompts = []
    for spec in SETS:
        answers = assign_ordered(_entries(spec["answers"]), spec["gem"])
        prompt = {
            "id": spec["id"],
            "text": spec["text"],
            "category": spec["category"],
            "source": "curated",
            "answers": answers,
        }
        cleaned, errors = publishable(prompt)
        if errors:
            raise RuntimeError(f"{spec['id']}: {errors}")
        prompts.append(cleaned)
    return prompts
