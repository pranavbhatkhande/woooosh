"""Quality gates and alias repair for a single prompt."""

from __future__ import annotations

from pipeline.normalize import candidates, normalize, within_one_edit
from pipeline.profanity import contains_profanity
from pipeline.tiering import GEM_TIER, TIER_IDS, histogram

MIN_ANSWERS = 40
MAX_TIER_FRACTION = 0.45


def repair_answers(answers: list[dict]) -> list[dict]:
    """Drop colliding aliases and the less popular side of a canonical clash."""
    grouped: dict[str, dict] = {}
    for row in answers:
        key = normalize(row.get("name", ""))
        if not key:
            continue
        current = grouped.get(key)
        if current is None or float(row.get("popularity", 0)) > float(current.get("popularity", 0)):
            kept = dict(row)
            kept["aliases"] = list(row.get("aliases") or [])
            grouped[key] = kept
    rows = list(grouped.values())
    # An alias that is somebody else's name has to go before that name is dropped,
    # or the survivor inherits a key that used to belong to a different answer.
    claimed = set()
    for row in rows:
        claimed |= candidates(normalize(row.get("name", "")))
    for row in rows:
        owner = normalize(row.get("name", ""))
        row["aliases"] = [
            alias for alias in row.get("aliases") or []
            if normalize(alias) and normalize(alias) not in claimed - {owner}
        ]
    rows = _drop_near_canonicals(rows)
    _claim_aliases(rows)
    return rows


def _claim_aliases(rows: list[dict]) -> None:
    """First canonical forms, then aliases. A key can belong to only one answer."""
    claimed: dict[str, str] = {}
    for row in rows:
        for form in candidates(normalize(row.get("name", ""))):
            claimed.setdefault(form, row.get("name", ""))
    for row in rows:
        owner = row.get("name", "")
        kept = []
        seen = set()
        for alias in row.get("aliases") or []:
            key = normalize(alias)
            if not key or key in seen or contains_profanity(alias) or len(alias) > 40:
                continue
            forms = candidates(key)
            if any(claimed.get(form) not in (None, owner) for form in forms):
                continue
            if any(
                other != owner and within_one_edit(key, other_key) and len(key) >= 6 and len(other_key) >= 6
                for other_key, other in ((normalize(candidate.get("name", "")), candidate.get("name", "")) for candidate in rows)
            ):
                continue
            for form in forms:
                claimed[form] = owner
            seen.add(key)
            kept.append(alias.strip())
        row["aliases"] = kept[:6]


def _drop_near_canonicals(rows: list[dict]) -> list[dict]:
    drop: set[int] = set()
    keys = [(index, normalize(row.get("name", ""))) for index, row in enumerate(rows)]
    for left in range(len(keys)):
        if left in drop:
            continue
        left_index, left_key = keys[left]
        left_forms = candidates(left_key)
        for right in range(left + 1, len(keys)):
            if right in drop:
                continue
            right_index, right_key = keys[right]
            clash = False
            if left_forms & candidates(right_key):
                clash = True
            elif (
                len(left_key) >= 6
                and len(right_key) >= 6
                and abs(len(left_key) - len(right_key)) <= 1
                and left_key != right_key
                and within_one_edit(left_key, right_key)
            ):
                clash = True
            if not clash:
                continue
            left_pop = float(rows[left_index].get("popularity", 0))
            right_pop = float(rows[right_index].get("popularity", 0))
            loser = right if (right_pop, rows[right_index].get("name", "")) < (
                left_pop,
                rows[left_index].get("name", ""),
            ) else left
            # On a popularity tie, drop the later name so the result is stable.
            if right_pop == left_pop:
                loser = right if rows[right_index].get("name", "") > rows[left_index].get("name", "") else left
            drop.add(loser)
    return [row for index, row in enumerate(rows) if index not in drop]


def _clean_aliases(row: dict, rows: list[dict]) -> list[str]:
    owner = normalize(row.get("name", ""))
    taken = {}
    for other in rows:
        if other is row:
            continue
        taken[normalize(other.get("name", ""))] = other.get("name")
        for form in candidates(normalize(other.get("name", ""))):
            taken.setdefault(form, other.get("name"))
    cleaned = []
    seen = {owner}
    for alias in row.get("aliases") or []:
        key = normalize(alias)
        if not key or key in seen or key in taken:
            continue
        if contains_profanity(alias):
            continue
        if len(key) < 2 or len(alias) > 40:
            continue
        if any(within_one_edit(key, other) and abs(len(key) - len(other)) <= 1 and len(key) >= 6 and len(other) >= 6 for other in taken):
            continue
        seen.add(key)
        cleaned.append(alias.strip())
    return cleaned[:6]


def evaluate(prompt: dict) -> list[str]:
    issues = []
    text = (prompt.get("text") or "").strip()
    if len(text) < 12:
        issues.append("text-too-short")
    if len(text) > 110:
        issues.append("text-too-long")
    if contains_profanity(text):
        issues.append("text-profanity")
    answers = prompt.get("answers") or []
    if len(answers) < MIN_ANSWERS:
        issues.append(f"too-few:{len(answers)}")
    counts = histogram(answers)
    for tier in TIER_IDS:
        if counts.get(tier, 0) < 1:
            issues.append(f"missing-tier:{tier}")
    if answers and max(counts.values()) / len(answers) > MAX_TIER_FRACTION:
        issues.append("tier-skew")
    gems = [row for row in answers if row.get("gem")]
    if len(gems) != 1:
        issues.append(f"gem-count:{len(gems)}")
    elif gems[0].get("tier") != GEM_TIER:
        issues.append("gem-not-apex")
    seen = {}
    for row in answers:
        name = row.get("name") or ""
        if not name.strip():
            issues.append("blank-name")
            continue
        if contains_profanity(name) or any(contains_profanity(alias) for alias in row.get("aliases") or []):
            issues.append(f"profanity:{name}")
        for key in candidates(normalize(name)):
            prior = seen.get(key)
            if prior and prior != name:
                issues.append(f"collision:{prior}|{name}")
            seen.setdefault(key, name)
        for alias in row.get("aliases") or []:
            key = normalize(alias)
            prior = seen.get(key)
            if prior and prior != name:
                issues.append(f"alias-collision:{alias}")
            if key:
                seen.setdefault(key, name)
    return issues
