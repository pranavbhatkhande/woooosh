"""Keep this in lockstep with js/match.js. Shared cases live in tests/fixtures."""

from __future__ import annotations

import re
import unicodedata

ARTICLE = re.compile(r"^(?:a|an|the)\s+")
HYPHEN = re.compile(r"[‐‑‒–—-]")
MARKS = re.compile(r"\s+")

_SPECIAL = (
    (re.compile(r"c\+\+"), "c plus plus"),
    (re.compile(r"c#"), "c sharp"),
    (re.compile(r"f#"), "f sharp"),
    (re.compile(r"\br\s*&\s*b\b"), "r and b"),
)


def normalize(raw: object) -> str:
    text = str(raw or "").strip().lower()
    if not text:
        return ""
    for pattern, repl in _SPECIAL:
        text = pattern.sub(repl, text)
    text = re.sub(r"\s+&\s+", " and ", text)
    text = re.sub(r"\s+&", " and ", text)
    text = re.sub(r"&\s+", " and ", text)
    text = text.replace("&", "")
    text = (
        text.replace("ß", "ss")
        .replace("æ", "ae")
        .replace("œ", "oe")
        .replace("ø", "o")
        .replace("ł", "l")
        .replace("đ", "d")
        .replace("þ", "th")
    )
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if not unicodedata.category(ch).startswith("M"))
    text = text.replace("'", "").replace("’", "")
    text = HYPHEN.sub(" ", text)
    text = "".join(ch if ch.isalnum() or ch.isspace() else "" for ch in text)
    text = MARKS.sub(" ", text).strip()
    while ARTICLE.match(text):
        text = ARTICLE.sub("", text)
    return text.strip()


def variants(norm: str) -> set[str]:
    out: set[str] = set()
    if not norm or len(norm) < 4:
        return out

    def add(value: str) -> None:
        if value and value != norm and len(value) >= 2:
            out.add(value)

    if norm.endswith("s") and not norm.endswith("ss"):
        add(norm[:-1])
    if norm.endswith("es"):
        add(norm[:-2])
    if norm.endswith("ies"):
        add(norm[:-3] + "y")
    if re.search(r"[^aeiou]y$", norm):
        add(norm[:-1] + "ies")
    elif re.search(r"(?:s|x|z|ch|sh)$", norm):
        add(norm + "es")
    elif not norm.endswith("s"):
        add(norm + "s")
    return out


def plural_root(norm: str) -> str | None:
    """A high-confidence singular. Used to merge 'shark'/'sharks', not 'paris'/'pari'."""
    if norm in {"species", "series", "news"} or len(norm) < 5:
        return None
    if norm.endswith("ies") and len(norm) > 5:
        stem = norm[:-3]
        if stem and stem[-1] not in "aeiou":
            return stem + "y"
    if norm.endswith("es") and norm.endswith(("ches", "shes", "sses", "xes", "zes")):
        return norm[:-2]
    if norm.endswith("s") and not norm.endswith(("ss", "is", "us", "ous", "ics")):
        root = norm[:-1]
        if len(root) >= 3 and root[-1] not in "iua":
            return root
    return None


def keys_for(name: str, aliases: list[str] | None = None) -> set[str]:
    """Exact keys plus a compacted form. Plurals are handled by plural_root, not here."""
    keys: set[str] = set()
    for raw in [name, *(aliases or [])]:
        norm = normalize(raw)
        if not norm:
            continue
        keys.add(norm)
        compact = norm.replace(" ", "")
        if len(compact) >= 7 and compact != norm:
            keys.add(compact)
    return keys
