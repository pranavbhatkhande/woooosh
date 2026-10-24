"""Percentile tiers for generated prompts, and a fixed map for AI familiarity."""

from __future__ import annotations

TIER_ORDER = ["taxi", "climb", "burn", "stall", "apogee", "escape"]
TIER_POINTS = {"taxi": 5, "climb": 10, "burn": 25, "stall": 40, "apogee": 60, "escape": 100}

# Rarity 0 is the most common answer. Cuts are exclusive upper bounds.
# The head stays small so a long, exhaustive tail lands in STALL and APOGEE.
TIER_CUTS = (
    (0.07, "taxi"),
    (0.18, "climb"),
    (0.36, "burn"),
    (0.52, "stall"),
    (0.995, "apogee"),
    (1.01, "escape"),
)

ORDERED_WEIGHTS = (0.20, 0.22, 0.22, 0.18, 0.18)
ORDERED_TIERS = ("taxi", "climb", "burn", "stall", "apogee")


def tier_for_rarity(rarity: float) -> str:
    for cut, name in TIER_CUTS:
        if rarity < cut:
            return name
    return "escape"


def tier_for_familiarity(value: float) -> str:
    """Map 1 (obscure) through 10 (universal). Never returns the gem tier."""
    try:
        number = int(round(float(value)))
    except (TypeError, ValueError) as exc:
        raise ValueError("familiarity must be numeric") from exc
    familiarity = max(1, min(10, number))
    if familiarity >= 9:
        return "taxi"
    if familiarity >= 7:
        return "climb"
    if familiarity >= 5:
        return "burn"
    if familiarity >= 3:
        return "stall"
    return "apogee"


def allocate(count: int, weights: tuple[float, ...] = ORDERED_WEIGHTS) -> list[int]:
    if count < len(weights):
        raise ValueError(f"need at least {len(weights)} answers to fill tiers")
    raw = [weight * count for weight in weights]
    base = [int(value) for value in raw]
    remainder = count - sum(base)
    fraction_order = sorted(range(len(weights)), key=lambda i: (raw[i] - base[i], -i), reverse=True)
    for index in fraction_order:
        if remainder <= 0:
            break
        base[index] += 1
        remainder -= 1
    guard = 0
    while any(value == 0 for value in base) and guard < 10:
        guard += 1
        empty = next(i for i, value in enumerate(base) if value == 0)
        donor = max(range(len(base)), key=lambda i: base[i])
        if base[donor] <= 1:
            break
        base[donor] -= 1
        base[empty] += 1
    return base


def _median(values: list[float]) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2


def pick_gem(ranked: list[dict]) -> dict:
    """High rarity, still recognizable: not the noisiest tail and not a famous pick."""
    links = sorted(int(answer.get("sitelinks") or 0) for answer in ranked)

    def percentile(fraction: float) -> float:
        if not links:
            return 0
        index = min(len(links) - 1, max(0, int(round(fraction * (len(links) - 1)))))
        return links[index]

    low = max(8, percentile(0.12))
    high = max(low, percentile(0.58))
    band = [
        answer
        for answer in ranked
        if 0.78 <= answer["rarity"] <= 0.95 and low <= int(answer.get("sitelinks") or 0) <= high
    ]
    if not band:
        band = [
            answer
            for answer in ranked
            if answer["rarity"] >= 0.75 and int(answer.get("sitelinks") or 0) >= low
        ]
    if not band:
        band = ranked[-3:] or ranked
    # Aim at the rare-but-still-linked part of the pool, not the noisiest tail
    # and not the most famous member of that band.
    band.sort(key=lambda answer: (abs(answer["rarity"] - 0.88), -int(answer.get("sitelinks") or 0)))
    return band[0]


def assign_by_popularity(answers: list[dict]) -> list[dict]:
    """Higher `pop` is more common. One gem, and every other escape candidate drops to apogee."""
    if len(answers) < 6:
        raise ValueError("not enough answers to tier")
    ranked = sorted(answers, key=lambda answer: (-float(answer.get("pop") or 0), answer["name"].lower()))
    last = len(ranked) - 1
    for index, answer in enumerate(ranked):
        rarity = index / last if last else 0.0
        answer["rarity"] = rarity
        answer["tier"] = tier_for_rarity(rarity)
        answer["gem"] = False
    gem = pick_gem(ranked)
    for answer in ranked:
        if answer is gem:
            answer["tier"] = "escape"
            answer["gem"] = True
        elif answer["tier"] == "escape":
            answer["tier"] = "apogee"
    return ranked


def assign_ordered(entries: list[dict], gem_name: str) -> list[dict]:
    """entries are already ordered from most common to rarest. gem_name is forced to escape."""
    from pipeline.normalize import normalize

    gem_key = normalize(gem_name)
    rest: list[dict] = []
    gem: dict | None = None
    for entry in entries:
        if normalize(entry["name"]) == gem_key and gem is None:
            gem = entry
        else:
            rest.append(entry)
    if gem is None:
        raise ValueError(f"gem not in answers: {gem_name}")
    counts = allocate(len(rest))
    answers: list[dict] = []
    cursor = 0
    for tier, count in zip(ORDERED_TIERS, counts):
        for entry in rest[cursor : cursor + count]:
            answers.append({**entry, "tier": tier, "gem": False})
        cursor += count
    answers.append({**gem, "tier": "escape", "gem": True})
    return answers


def popularity_score(sitelinks: int, zipf: float) -> float:
    import math

    return math.log1p(max(0, sitelinks)) * 2.0 + 0.15 * max(0.0, zipf)
