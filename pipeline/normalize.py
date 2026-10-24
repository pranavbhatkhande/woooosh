"""Text normalization shared with js/matcher.js. Keep the rules aligned."""

from __future__ import annotations

import re
import unicodedata

EXCEPTIONS = {
    "species",
    "series",
    "news",
    "maths",
    "lens",
    "mess",
    "atlas",
    "chaos",
    "metropolis",
    "epidermis",
    "alias",
    "gas",
    "bus",
    "this",
    "plus",
}

_FOLD = (
    ("æ", "ae"),
    ("œ", "oe"),
    ("ø", "o"),
    ("ł", "l"),
    ("ß", "ss"),
    ("đ", "d"),
    ("þ", "th"),
    ("ð", "d"),
    ("Æ", "ae"),
    ("Œ", "oe"),
    ("Ø", "o"),
    ("Ł", "l"),
    ("Đ", "d"),
    ("Þ", "th"),
    ("Ð", "d"),
)


def fold_accents(value: str) -> str:
    text = value
    for src, dst in _FOLD:
        text = text.replace(src, dst)
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize(raw: str | None) -> str:
    if raw is None:
        return ""
    text = fold_accents(str(raw)).lower()
    text = text.replace("&", " and ").replace("+", " and ")
    text = text.replace("'", "").replace("’", "")
    text = re.sub(r"[\u2010-\u2015\-_/]+", " ", text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    match = re.match(r"^(?:the|a|an)\s+(.+)$", text)
    if match:
        text = match.group(1)
    return text


def word_variants(word: str) -> list[str]:
    if not word or len(word) <= 3 or word in EXCEPTIONS:
        return []
    variants: list[str] = []
    if word.endswith("ies") and len(word) > 4:
        variants.append(word[:-3] + "y")
    if re.search(r"(?:ches|shes|xes|zes|sses|ses)$", word) and len(word) > 4:
        variants.append(word[:-2])
    if re.search(r"[^aeiou]s$", word) and not word.endswith("ss"):
        variants.append(word[:-1])
    if word.endswith("es") and len(word) > 4:
        stem = word[:-1]
        if stem.endswith("e"):
            variants.append(stem)
    return [variant for variant in variants if variant and variant != word and len(variant) >= 2]


def candidates(phrase: str) -> set[str]:
    forms = set()
    if not phrase:
        return forms
    forms.add(phrase)
    parts = phrase.split(" ")
    word = parts[-1]
    for variant in word_variants(word):
        forms.add(" ".join(parts[:-1] + [variant]))
    return {form for form in forms if form}


def within_one_edit(a: str, b: str) -> bool:
    if a == b:
        return True
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        index = 0
        while index < la and a[index] == b[index]:
            index += 1
        if index == la:
            return True
        if index + 1 < la and a[index] == b[index + 1] and a[index + 1] == b[index]:
            return a[index + 2 :] == b[index + 2 :]
        return a[index + 1 :] == b[index + 1 :]
    shorter, longer = (a, b) if la < lb else (b, a)
    i = j = skipped = 0
    while i < len(shorter) and j < len(longer):
        if shorter[i] == longer[j]:
            i += 1
            j += 1
        else:
            skipped += 1
            if skipped > 1:
                return False
            j += 1
    return True
