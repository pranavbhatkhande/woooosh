"""Whole-token filter. Substrings are left alone so Assam, cocktail, and Scunthorpe stay."""

from __future__ import annotations

from pipeline.normalize import normalize

BANNED = {
    "fuck",
    "fucking",
    "fucked",
    "fucker",
    "motherfucker",
    "shit",
    "shitty",
    "bullshit",
    "cunt",
    "nigger",
    "nigga",
    "faggot",
    "fag",
    "retard",
    "retarded",
    "slut",
    "whore",
    "porn",
    "porno",
    "rape",
    "rapist",
    "kike",
    "spic",
    "chink",
    "gook",
    "wetback",
    "tranny",
    "asshole",
    "dickhead",
    "jizz",
    "cumshot",
    "blowjob",
    "sex",
    "sexy",
}

PHRASES = (
    "blow job",
    "child porn",
    "kiddie porn",
)


def contains_profanity(text: str) -> bool:
    folded = normalize(text)
    if not folded:
        return False
    tokens = set(folded.split())
    if tokens & BANNED:
        return True
    return any(phrase in folded for phrase in PHRASES)
