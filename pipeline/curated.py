"""Hand-authored prompts live in pipeline/curated/prompts.txt."""

from __future__ import annotations

from pipeline.naming import acceptable_label
from pipeline.paths import CURATED_PATH
from pipeline.tiering import POINTS

_TIER_POPULARITY = {"pad": 600, "ascent": 500, "ceiling": 400, "hotshot": 300, "orbit": 200, "apex": 100}


def load_curated(path=CURATED_PATH) -> list[dict]:
    if not path.exists():
        return []
    return [_public(prompt) for prompt in parse_curated(path.read_text(encoding="utf-8"))]


def parse_curated(text: str) -> list[dict]:
    prompts = []
    block: list[str] | None = None
    for line in text.splitlines():
        if line.strip() == "---":
            if block:
                prompts.append(_parse_block(block))
            block = []
            continue
        if block is not None:
            block.append(line)
    if block:
        prompts.append(_parse_block(block))
    return [prompt for prompt in prompts if prompt]


def _parse_block(lines: list[str]) -> dict | None:
    header: dict[str, str] = {}
    answers = []
    in_header = True
    tier_seen: dict[str, int] = {tier: 0 for tier in POINTS}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if in_header and ":" in line and "|" not in line:
            key, value = line.split(":", 1)
            header[key.strip().lower()] = value.strip()
            continue
        in_header = False
        parts = [part.strip() for part in line.split("|")]
        if len(parts) < 2:
            continue
        name, tier = parts[0], parts[1].lower()
        aliases = [alias.strip() for alias in parts[2].split(";") if alias.strip()] if len(parts) > 2 and parts[2] else []
        gem = len(parts) > 3 and parts[3].lower() == "gem"
        if tier not in POINTS or not acceptable_label(name):
            continue
        tier_seen[tier] += 1
        answers.append({
            "name": name,
            "aliases": aliases,
            "tier": tier,
            "gem": gem,
            "popularity": _TIER_POPULARITY[tier] - tier_seen[tier],
        })
    if not header.get("id") or not header.get("text"):
        return None
    return {
        "id": header["id"],
        "text": header["text"],
        "category": header.get("category") or "everyday",
        "source": "hand",
        "answers": answers,
    }


def _public(prompt: dict) -> dict:
    return {
        "id": prompt["id"],
        "text": prompt["text"],
        "category": prompt["category"],
        "source": "hand",
        "answers": [
            {
                "name": answer["name"],
                "aliases": list(answer.get("aliases") or []),
                "tier": answer["tier"],
                "gem": bool(answer.get("gem")),
            }
            for answer in prompt["answers"]
        ],
    }
