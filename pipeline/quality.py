"""Gates a prompt must clear before it can ship in the bank."""

from __future__ import annotations

from collections import Counter

from pipeline.normalize import keys_for, normalize, plural_root
from pipeline.profanity import is_profane
from pipeline.tiers import TIER_ORDER

MIN_ANSWERS = 40
MAX_ANSWER_CHARS = 60
MAX_PROMPT_CHARS = 90


def repair_answers(answers: list[dict]) -> list[dict]:
    """Merge plural duplicates and drop aliases that collide with another answer."""
    merged: list[dict] = []
    by_key: dict[str, dict] = {}
    for answer in answers:
        name = (answer.get("name") or "").strip()
        if not name:
            continue
        canonical = normalize(name)
        if not canonical:
            continue
        aliases = []
        for alias in answer.get("aliases") or []:
            if alias and normalize(alias) and normalize(alias) != canonical:
                aliases.append(alias.strip())
        item = {
            "name": name,
            "aliases": aliases,
            "tier": answer.get("tier"),
            "gem": bool(answer.get("gem")),
            "pop": answer.get("pop", 0),
            "sitelinks": answer.get("sitelinks", 0),
            "qid": answer.get("qid"),
        }
        found = None
        own_keys = keys_for(name, [])
        root = plural_root(canonical)
        if root:
            own_keys.add(root)
        for key in own_keys:
            if key in by_key:
                found = by_key[key]
                break
        if found is None and canonical in {plural_root(key) for key in by_key}:
            for key, owner in by_key.items():
                if plural_root(key) == canonical:
                    found = owner
                    break
        if found is None:
            merged.append(item)
            for key in own_keys:
                by_key.setdefault(key, item)
            continue
        if float(item["pop"] or 0) > float(found["pop"] or 0):
            found["name"] = item["name"]
            found["qid"] = item["qid"] or found.get("qid")
        found["pop"] = max(float(found["pop"] or 0), float(item["pop"] or 0))
        found["sitelinks"] = max(int(found["sitelinks"] or 0), int(item["sitelinks"] or 0))
        if item["gem"]:
            found["gem"] = True
        for alias in [item["name"], *item["aliases"]]:
            if normalize(alias) != normalize(found["name"]):
                found["aliases"].append(alias)

    canonical = {normalize(answer["name"]): answer for answer in merged}
    wanted: dict[str, list[dict]] = {}
    for answer in merged:
        for alias in answer["aliases"]:
            norm = normalize(alias)
            if norm:
                wanted.setdefault(norm, []).append(answer)
    blocked = set()
    for norm, owners in wanted.items():
        distinct = {id(owner) for owner in owners}
        owner = canonical.get(norm)
        if len(distinct) > 1 or (owner is not None and any(item is not owner for item in owners)):
            blocked.add(norm)

    for answer in merged:
        own = keys_for(answer["name"], [])
        kept: list[str] = []
        seen_alias: set[str] = set()
        for alias in answer["aliases"]:
            norm = normalize(alias)
            if not norm or norm in seen_alias or norm in own or norm in blocked:
                continue
            if norm in canonical and canonical[norm] is not answer:
                continue
            kept.append(alias.strip())
            seen_alias.add(norm)
        answer["aliases"] = kept
    return merged


def lint_prompt(prompt: dict) -> list[str]:
    errors: list[str] = []
    text = (prompt.get("text") or "").strip()
    if not text or len(text) > MAX_PROMPT_CHARS:
        errors.append("bad prompt text")
    if is_profane(text):
        errors.append("profane prompt")
    lowered = text.lower()
    if not lowered.startswith("name a") and not lowered.startswith("name an"):
        errors.append("prompt must start with Name a/an")
    if " or " in lowered or "?" in text:
        errors.append("ambiguous prompt wording")

    answers = prompt.get("answers") or []
    if len(answers) < MIN_ANSWERS:
        errors.append(f"only {len(answers)} answers")

    seen = set()
    tiers: Counter[str] = Counter()
    gems = 0
    for answer in answers:
        name = (answer.get("name") or "").strip()
        norm = normalize(name)
        if not norm or len(name) > MAX_ANSWER_CHARS:
            errors.append(f"bad answer name {name!r}")
            continue
        if is_profane(name) or any(is_profane(alias) for alias in answer.get("aliases") or []):
            errors.append(f"profane answer {name}")
        if norm in seen:
            errors.append(f"duplicate answer {name}")
        seen.add(norm)
        tier = answer.get("tier")
        if tier not in TIER_ORDER:
            errors.append(f"bad tier on {name}")
        else:
            tiers[tier] += 1
        if answer.get("gem"):
            gems += 1
            if tier != "escape":
                errors.append("gem is not escape")
    if gems != 1:
        errors.append(f"gem count {gems}")
    if tiers.get("escape") != 1:
        errors.append(f"escape count {tiers.get('escape', 0)}")
    for tier in TIER_ORDER:
        if tier != "escape" and tiers.get(tier, 0) < 1:
            errors.append(f"missing tier {tier}")

    claimed: dict[str, str] = {}
    for answer in answers:
        for key in keys_for(answer.get("name") or "", answer.get("aliases") or []):
            if key in claimed and claimed[key] != answer.get("name"):
                errors.append(f"alias collision {key!r}")
                break
            claimed.setdefault(key, answer.get("name") or "")
    return errors


def publishable(prompt: dict) -> tuple[dict, list[str]]:
    """Return a client-shaped prompt, or errors. Strips generator-only fields."""
    from pipeline.tiers import TIER_ORDER

    cleaned = {
        "id": prompt["id"],
        "text": prompt["text"].strip(),
        "category": prompt.get("category") or "general",
        "source": prompt.get("source") or "unknown",
        "answers": [],
    }
    rank = {tier: index for index, tier in enumerate(TIER_ORDER)}
    ordered = sorted(
        prompt.get("answers") or [],
        key=lambda answer: (rank.get(answer.get("tier"), 99), -float(answer.get("pop") or 0), answer.get("name") or ""),
    )
    for answer in ordered:
        cleaned["answers"].append(
            {
                "name": answer["name"].strip(),
                "aliases": [alias.strip() for alias in (answer.get("aliases") or []) if alias and alias.strip()],
                "tier": answer["tier"],
                "gem": bool(answer.get("gem")),
            }
        )
    errors = lint_prompt(cleaned)
    return cleaned, errors
