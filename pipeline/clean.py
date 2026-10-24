"""Turn Wikipedia titles into answer labels."""

from __future__ import annotations

import re

DISAMB = re.compile(r"^(.*?) \(([^)]+)\)$")
DISAMB_TOKENS = (
    "film",
    "album",
    "series",
    "game",
    "song",
    "novel",
    "band",
    "group",
    "character",
    "moon",
    "comic",
    "play",
    "opera",
    "musical",
    "tv",
    "miniseries",
    "book",
    "disambiguation",
    "dog",
    "cat",
    "horse",
    "element",
    "state",
    "city",
    "breed",
    "club",
    "programming",
    "language",
    "mountain",
    "island",
    "river",
    "lake",
)
BAD_STARTS = (
    "list of",
    "index of",
    "outline of",
    "glossary of",
    "timeline of",
    "history of",
    "comparison of",
    "rankings of",
    "template:",
    "category:",
    "portal:",
    "wikipedia:",
)
BROADCAST = re.compile(
    r"\b(?:on|via) (?:nbc|abc|cbs|fox|hbo|espn|bbc|itv|pbs|cnn|msnbc|sky|netflix)\b",
    re.IGNORECASE,
)


def clean_title(title: str) -> str:
    text = (title or "").replace("_", " ").strip()
    match = DISAMB.match(text)
    if not match:
        return text
    inner = match.group(2).lower()
    if any(token in inner for token in DISAMB_TOKENS) or re.search(r"\d{3,4}", inner):
        return match.group(1).strip()
    return text


def junk_title(title: str, ban: list[str] | None = None) -> bool:
    low = (title or "").strip().lower()
    if not low or any(low.startswith(prefix) for prefix in BAD_STARTS):
        return True
    if "disambiguation" in low or BROADCAST.search(low):
        return True
    for needle in ban or []:
        if needle.lower() in low:
            return True
    return False
