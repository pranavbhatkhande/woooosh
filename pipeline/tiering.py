"""Map popularity to the six WOOOOSH tiers.

Keep ids and points aligned with js/tiers.js.
Index 0 is the most common answer. Hotshot is the upper-middle band:
the clever-sounding pick that is not actually rare.
"""

from __future__ import annotations

import math

TIER_ORDER = (
    ("pad", 5, 0.18),
    ("ascent", 10, 0.36),
    ("ceiling", 25, 0.55),
    ("hotshot", 40, 0.73),
    ("orbit", 60, 0.89),
    ("apex", 100, 1.01),
)

TIER_IDS = tuple(tier[0] for tier in TIER_ORDER)
POINTS = {tier: points for tier, points, _cut in TIER_ORDER}
TRAP_TIER = "hotshot"
GEM_TIER = "apex"

# Answers whose label fails this check can still be apex, but they lose the gem.
_GEM_MAX_WORDS = 5
_GEM_MAX_CHARS = 32


def tier_for_rank(index: int, count: int) -> str:
    if count <= 0:
        raise ValueError("count must be positive")
    fraction = index / count
    for tier, _points, cut in TIER_ORDER:
        if fraction < cut:
            return tier
    return TIER_ORDER[-1][0]


def rarity_score(sitelinks: int, label: str = "", pageviews: int | None = None, zipf: float | None = None) -> float:
    """Higher means more common. Sitelinks lead; wordfreq and pageviews nudge."""
    score = math.log1p(max(0, int(sitelinks)))
    if zipf is None and label and len(label) >= 4:
        zipf = _zipf(label)
    if zipf:
        score += 0.12 * float(zipf)
    if pageviews is not None:
        score += 0.35 * math.log10(max(0, int(pageviews)) + 1)
    return score


def familiarity_score(familiarity: int, zipf: float = 0.0) -> float:
    """LLM familiarity is 1 (everyone blurts it) through 6 (rarely). Higher score = more common."""
    clamped = min(6, max(1, int(familiarity)))
    return (7 - clamped) + 0.2 * float(zipf or 0)


def _zipf(label: str) -> float:
    try:
        from wordfreq import zipf_frequency
    except ImportError:
        return 0.0
    return float(zipf_frequency(label.lower(), "en"))


def assign_tiers(answers: list[dict]) -> list[dict]:
    """Set tier and gem from popularity. Most popular item is Pad. Mutates and returns the list."""
    ordered = sorted(answers, key=lambda row: (-float(row.get("popularity", 0)), row.get("name", "")))
    count = len(ordered)
    for index, row in enumerate(ordered):
        row["tier"] = tier_for_rank(index, count)
        row["gem"] = False
    _apply_showoff_pins(ordered)
    _ensure_tiers(ordered)
    gem_name = choose_gem(ordered)
    for row in ordered:
        row["gem"] = row.get("name") == gem_name
    return ordered


def choose_gem(answers: list[dict]) -> str | None:
    apex = [row for row in answers if row.get("tier") == GEM_TIER and not row.get("showoff")]
    if not apex:
        apex = [row for row in answers if row.get("tier") == GEM_TIER]
    if not apex:
        return None
    pool = [row for row in apex if _gem_name_ok(row.get("name", ""))] or apex
    pool.sort(key=lambda row: (-float(row.get("popularity", 0)), row.get("name", "")))
    return pool[0]["name"]


def _gem_name_ok(name: str) -> bool:
    if not name or len(name) > _GEM_MAX_CHARS or len(name.split()) > _GEM_MAX_WORDS:
        return False
    if any(ch.isdigit() for ch in name):
        return False
    lowered = name.lower()
    if "disambiguation" in lowered or lowered.startswith("list "):
        return False
    return True


def _apply_showoff_pins(answers: list[dict]) -> None:
    pinned = [row for row in answers if row.get("showoff")]
    if not pinned:
        return
    for row in pinned:
        row["tier"] = TRAP_TIER
        row["gem"] = False


def _ensure_tiers(answers: list[dict]) -> None:
    if not answers:
        return
    for tier in TIER_IDS:
        if any(row.get("tier") == tier for row in answers):
            continue
        donor = max(TIER_IDS, key=lambda candidate: sum(1 for row in answers if row.get("tier") == candidate))
        pool = [row for row in answers if row.get("tier") == donor and not row.get("showoff")]
        if not pool:
            pool = [row for row in answers if row.get("tier") == donor]
        if len(pool) <= 1 and donor != tier:
            continue
        if TIER_IDS.index(tier) > TIER_IDS.index(donor):
            pick = min(pool, key=lambda row: (float(row.get("popularity", 0)), row.get("name", "")))
        else:
            pick = max(pool, key=lambda row: (float(row.get("popularity", 0)), row.get("name", "")))
        pick["tier"] = tier


def histogram(answers: list[dict]) -> dict[str, int]:
    counts = {tier: 0 for tier in TIER_IDS}
    for row in answers:
        tier = row.get("tier")
        if tier in counts:
            counts[tier] += 1
    return counts
