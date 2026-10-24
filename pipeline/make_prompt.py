"""Score, tier, and validate one prompt."""

from __future__ import annotations

import re

from pipeline.clean import clean_title, junk_title
from pipeline.profanity import is_profane
from pipeline.quality import publishable, repair_answers
from pipeline.tiers import assign_by_popularity, popularity_score

try:
    from wordfreq import zipf_frequency
except ImportError:  # pragma: no cover - optional at runtime
    zipf_frequency = None

COMMA_PLACE = re.compile(r"^([^,]{2,40}),\s+[A-Z]")


def _has_name(answers: list[dict], expected: str) -> bool:
    needle = expected.lower()
    for answer in answers:
        name = answer["name"].lower()
        if len(needle) < 4:
            padded = f" {name} "
            if f" {needle} " in padded:
                return True
        elif needle in name:
            return True
    return False


def _zipf(name: str) -> float:
    if not zipf_frequency:
        return 0.0
    try:
        return float(zipf_frequency(name, "en"))
    except Exception:
        return 0.0


def _extra_aliases(label: str, wiki: str) -> list[str]:
    aliases = []
    if wiki and wiki != label:
        aliases.append(wiki)
    match = COMMA_PLACE.match(label)
    if match:
        aliases.append(match.group(1))
    return aliases


def build_prompt(job: dict, raw_items: list[dict]) -> tuple[dict | None, str]:
    ban = job.get("ban") or []
    prepared = []
    for item in raw_items:
        source = item.get("label") or item.get("wiki") or ""
        label = clean_title(source)
        if junk_title(label, ban) or junk_title(source, ban):
            continue
        if is_profane(label) or len(label) < 2 or len(label) > 60:
            continue
        sitelinks = int(item.get("sitelinks") or 0)
        if sitelinks < int(job.get("min_links") or 1):
            continue
        aliases = list(item.get("aliases") or [])
        aliases.extend(_extra_aliases(label, clean_title(item.get("wiki") or "")))
        prepared.append(
            {
                "name": label,
                "aliases": aliases,
                "pop": popularity_score(sitelinks, _zipf(label)),
                "sitelinks": sitelinks,
                "qid": item.get("qid"),
            }
        )
    prepared = repair_answers(prepared)
    prepared.sort(key=lambda answer: (-float(answer["pop"]), answer["name"].lower()))
    cap = int(job.get("cap") or 80)
    if len(prepared) > cap:
        prepared = prepared[:cap]
    if len(prepared) < 40:
        return None, f"only {len(prepared)} usable answers"
    missing = [name for name in job.get("must") or [] if not _has_name(prepared, name)]
    if missing:
        return None, "missing expected " + ", ".join(missing)
    try:
        tiered = assign_by_popularity(prepared)
    except ValueError as exc:
        return None, str(exc)
    prompt = {
        "id": job["id"],
        "text": job["text"],
        "category": job.get("category") or "general",
        "source": "wikidata",
        "answers": tiered,
    }
    cleaned, errors = publishable(prompt)
    if errors:
        return None, "; ".join(errors[:6])
    return cleaned, ""
