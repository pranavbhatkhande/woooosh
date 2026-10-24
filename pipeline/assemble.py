"""Turn Wikidata rows into a gated prompt."""

from __future__ import annotations

from pipeline.naming import (
    acceptable_label,
    alias_is_useful,
    looks_scientific,
    present_alias,
    present_name,
)
from pipeline.normalize import normalize
from pipeline.quality import evaluate, repair_answers
from pipeline.tiering import assign_tiers, rarity_score

MIN_ANSWERS = 40


def assemble_prompt(template, bindings: list[dict], alias_map: dict[str, list[str]], pageviews: dict[str, int] | None = None):
    best: dict[str, dict] = {}
    for row in bindings:
        try:
            qid = row["item"]["value"].rsplit("/", 1)[-1]
            label = row["label"]["value"]
            sitelinks = int(float(row["sitelinks"]["value"]))
        except (KeyError, TypeError, ValueError):
            continue
        if sitelinks < template.min_sitelinks:
            continue
        current = best.get(qid)
        if current is None or sitelinks > current["sitelinks"]:
            best[qid] = {"qid": qid, "label": label, "sitelinks": sitelinks}

    by_name: dict[str, dict] = {}
    for item in best.values():
        name = present_name(item["label"])
        if not acceptable_label(name):
            continue
        key = normalize(name)
        if not key:
            continue
        aliases = _aliases_for(name, alias_map.get(item["qid"], []))
        views = None if pageviews is None else pageviews.get(item["qid"])
        row = {
            "name": name,
            "qid": item["qid"],
            "sitelinks": item["sitelinks"],
            "aliases": aliases,
            "popularity": rarity_score(item["sitelinks"], name, pageviews=views),
        }
        previous = by_name.get(key)
        if previous is None or row["sitelinks"] > previous["sitelinks"]:
            if previous:
                row["aliases"] = _merge_aliases(name, previous["aliases"], aliases)
            by_name[key] = row

    rows = sorted(by_name.values(), key=lambda row: (-row["sitelinks"], row["name"]))
    if len(rows) > template.limit:
        rows = rows[: template.limit]
    if looks_scientific([row["name"] for row in rows]):
        return None, ["scientific-names"]
    if len(rows) < MIN_ANSWERS:
        return None, [f"too-few:{len(rows)}"]

    repaired = repair_answers(rows)
    if len(repaired) < MIN_ANSWERS:
        return None, [f"too-few-after-repair:{len(repaired)}"]
    assign_tiers(repaired)
    prompt = {
        "id": f"wd-{template.id}",
        "text": template.text,
        "category": template.category,
        "source": "wikidata",
        "answers": [_public_answer(row) for row in repaired],
    }
    issues = evaluate(prompt)
    if issues:
        return None, issues
    return prompt, []


def _aliases_for(name: str, raw_aliases: list[str]) -> list[str]:
    owner = normalize(name)
    seen = {owner}
    kept = []
    for raw in raw_aliases:
        presented = present_alias(raw)
        key = normalize(presented)
        if not alias_is_useful(presented, key) or key in seen:
            continue
        seen.add(key)
        kept.append(presented)
    kept.sort(key=lambda alias: (len(alias), alias))
    return kept[:6]


def _merge_aliases(name: str, left: list[str], right: list[str]) -> list[str]:
    return _aliases_for(name, list(left) + list(right))


def _public_answer(row: dict) -> dict:
    answer = {
        "name": row["name"],
        "aliases": list(row.get("aliases") or []),
        "tier": row["tier"],
        "gem": bool(row.get("gem")),
    }
    if row.get("qid"):
        answer["qid"] = row["qid"]
    return answer
