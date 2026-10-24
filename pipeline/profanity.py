"""Token blocklist. Substrings are not matched, so 'classic' and 'Assam' stay."""

from __future__ import annotations

import re

from pipeline.normalize import normalize

# Unambiguous slurs and strong sexual profanity. Kept as tokens, not stems.
WORDS = {
    "fuck",
    "fucking",
    "fucker",
    "motherfucker",
    "shit",
    "shitty",
    "bullshit",
    "cunt",
    "bitch",
    "bastard",
    "asshole",
    "dickhead",
    "piss",
    "slut",
    "whore",
    "nigger",
    "nigga",
    "faggot",
    "fag",
    "retard",
    "retarded",
    "spic",
    "kike",
    "chink",
    "gook",
    "wetback",
    "tranny",
    "porn",
    "porno",
    "xxx",
}

TOKEN = re.compile(r"[a-z0-9]+")


def is_profane(text: str) -> bool:
    norm = normalize(text)
    if not norm:
        return False
    tokens = set(TOKEN.findall(norm))
    if tokens & WORDS:
        return True
    squashed = norm.replace(" ", "")
    return squashed in WORDS
