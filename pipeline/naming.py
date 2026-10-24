"""Label cleanup for Wikidata and model output."""

from __future__ import annotations

import re

from pipeline.profanity import contains_profanity

_SMALL = {"of", "the", "and", "a", "an", "in", "on", "for", "da", "de", "del", "van", "von", "di", "la", "le", "du"}
_TRAIL = re.compile(r"\s+\(([^)]{1,40})\)$")
_BINOMIAL = re.compile(r"^[A-Z][a-z]{2,} [a-z]{2,}$")
_ELEMENT = re.compile(r"(?i)^element\s+\d+$")
_STOP_ALIAS = {
    "a", "an", "the", "and", "or", "of", "in", "on", "to", "it", "is", "be", "at", "by",
    "we", "my", "no", "ok", "hi", "mr", "mrs", "dr", "st",
}


def title_case(name: str) -> str:
    parts = name.split(" ")
    out = []
    for index, part in enumerate(parts):
        if index and part.lower() in _SMALL:
            out.append(part.lower())
        elif part:
            out.append(part[:1].upper() + part[1:])
        else:
            out.append(part)
    return " ".join(out)


def strip_qualifier(label: str) -> str:
    name = re.sub(r"\s+", " ", label or "").strip()
    match = _TRAIL.search(name)
    if not match:
        return name
    inside = match.group(1).lower()
    if "disambiguation" in inside or len(inside) <= 32:
        return name[: match.start()].strip()
    return name


def present_name(label: str) -> str:
    name = strip_qualifier(label)
    letters = re.sub(r"[^A-Za-z]", "", name)
    if name.isupper() and len(letters) > 5:
        return title_case(name.lower())
    if name.islower():
        return title_case(name)
    return name


def present_alias(alias: str) -> str:
    text = strip_qualifier(alias)
    if not text or _ELEMENT.match(text):
        return ""
    letters = re.sub(r"[^A-Za-z]", "", text)
    if text.isupper() and 1 < len(letters) <= 5:
        return text
    if text.islower() and 1 < len(letters) <= 3 and text.isalpha():
        return text.upper()
    if text.islower():
        return title_case(text)
    return text


def acceptable_label(name: str) -> bool:
    if not name or len(name) < 2 or len(name) > 48:
        return False
    if len(name.split()) > 8:
        return False
    lowered = name.lower().strip()
    if lowered in {"unknown", "none", "n/a", "null", "other", "test", "deleted", "missing"}:
        return False
    if re.fullmatch(r"q\d+", lowered):
        return False
    # IUPAC temporary names (ununnilium, unbinilium, …) are not answers anyone can play.
    if re.match(r"un(?:nil|un|bi|tri|quad|pent|hex|sept|oct|enn)", lowered):
        return False
    if any(bad in lowered for bad in ("disambiguation", "list of ", "wikipedia:", "category:", "template:")):
        return False
    if contains_profanity(name):
        return False
    return bool(re.search(r"[a-z0-9]", lowered))


def looks_scientific(names: list[str]) -> bool:
    if len(names) < 10:
        return False
    hits = sum(1 for name in names if _BINOMIAL.match(name))
    return hits / len(names) >= 0.45


def alias_is_useful(alias: str, normalized: str) -> bool:
    if not alias or not normalized or len(normalized) < 2 or len(alias) > 40:
        return False
    if normalized in _STOP_ALIAS or _ELEMENT.match(alias):
        return False
    if re.search(r"\d", normalized):
        return False
    return not contains_profanity(alias)
