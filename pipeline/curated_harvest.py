"""Expand hand-curated prompts from exhaustive Wikipedia categories.

A harvest replaces the short hand list only when the category still contains
the famous answers we expect. Names that exist only on the hand list are
folded in afterwards, so a hand-picked gem is not thrown away. Failures leave
the hand list in place.
"""

from __future__ import annotations

import json

from pipeline.collect import collect_categories, enrich_entities
from pipeline.curated_loader import load_curated
from pipeline.make_prompt import build_prompt
from pipeline.net import CACHE
from pipeline.normalize import normalize

ACCEPTED = CACHE / "accepted"

# Categories chosen because the direct pages are the answers, not an index.
HARVEST = [
    {"id": "cur-spice", "categories": ["Spices"], "must": ["Black pepper"]},
    {"id": "cur-pasta", "categories": ["Types of pasta"], "must": ["Spaghetti"]},
    {"id": "cur-fruit", "categories": ["Edible fruits"], "must": ["Apple"]},
    {"id": "cur-vegetable", "categories": ["Leaf vegetables", "Root vegetables"], "must": ["Carrot"], "follow_geo": True},
    {"id": "cur-cheese", "categories": ["Types of cheese"], "must": ["Cheddar"], "follow_geo": True},
    {"id": "cur-cocktail", "categories": ["IBA official cocktails"], "must": ["Martini"]},
    {
        "id": "cur-candy",
        "categories": [
            "Brand name confectionery",
            "Chocolate bars",
            "British confectionery",
            "American confectionery",
        ],
        "must": ["Baby Ruth"],
        "follow_subcats": False,
        "min_answers": 80,
        "cap": 1800,
        "ban": ["list of", "company", "industry", "manufacturer"],
    },
    {"id": "cur-soda", "categories": ["Soft drinks"], "must": ["Coca-Cola"]},
    {
        "id": "cur-instrument",
        "categories": [
            "String instruments",
            "Electronic musical instruments",
            "Keyboard instruments",
            "Brass instruments",
            "Woodwind instruments",
            "Percussion instruments",
            "Plucked string instruments",
        ],
        "must": ["Piano"],
        "follow_subcats": False,
        "min_answers": 80,
        "cap": 1800,
        "ban": ["list of", "tuning", "notation", "technique", "repertoire", "manufacturer"],
    },
    {"id": "cur-board", "categories": ["Board games", "Abstract strategy games"], "must": ["Chess"]},
    {"id": "cur-language", "categories": ["Programming languages"], "must": ["Python"]},
    {
        "id": "cur-flower",
        "categories": [
            "Roses",
            "Iris (plant)",
            "Begonia",
            "Hibiscus",
            "Peonies",
            "Orchids",
            "Rose cultivars",
        ],
        "must": ["Rose"],
        "follow_subcats": False,
        "drop_binomial": True,
        "min_answers": 80,
        "cap": 1800,
        "ban": ["list of", "festival", "society", "rose hip", "rose water", "rose oil", "attar", "gardens", " list"],
    },
    {
        "id": "cur-tree",
        "categories": [
            "Fruit trees",
            "Trees of Europe",
        ],
        "must": ["Almond"],
        "follow_subcats": False,
        "drop_binomial": True,
        "min_answers": 80,
        "cap": 1800,
        "ban": ["list of", "arborist", "forestry", "timber", "of the year", "orchard"],
    },
    {"id": "cur-gemstone", "categories": ["Gemstones"], "must": ["Diamond"]},
    {"id": "cur-phobia", "categories": ["Phobias"], "must": ["Arachnophobia"]},
    {"id": "cur-greek", "categories": ["Greek mythological heroes"], "must": ["Heracles"]},
    {"id": "cur-moon", "categories": ["Moons of Jupiter", "Moons of Saturn", "Moons of Uranus", "Moons of Neptune"], "must": ["Europa"]},
    {"id": "cur-unit", "categories": ["Units of measurement"], "must": ["Metre"]},
    {"id": "cur-breakfast", "categories": ["Breakfast dishes"], "must": ["Pancake"]},
    {
        "id": "cur-park",
        "categories": [
            "National parks of the United States",
            "National parks of Canada",
            "National parks of Australia",
            "National parks of Japan",
            "National parks of China",
            "National parks of Thailand",
            "National parks of Brazil",
            "National parks of Mexico",
            "National parks of Indonesia",
            "National parks of Kenya",
            "National parks of Argentina",
            "National parks of Norway",
            "National parks of Spain",
            "National parks of France",
            "National parks of Germany",
            "National parks of Italy",
            "National parks of India",
            "National parks of South Africa",
            "National parks of New Zealand",
            "National parks of South Korea",
            "National parks of the United Kingdom",
            "National parks of Chile",
        ],
        "must": ["Inthanon"],
        "follow_subcats": False,
        "min_answers": 80,
        "cap": 1800,
        "ban": ["list of", "people", "superintendent", "in fiction", "highest", "building", "former", "service", "ranger"],
    },
]


def missing_hand_items(items: list[dict], hand_answers: list[dict]) -> list[dict]:
    """Hand answers the category did not return, shaped like collector rows."""
    seen: set[str] = set()
    for item in items:
        for field in (item.get("label"), item.get("wiki")):
            norm = normalize(field or "")
            if norm:
                seen.add(norm)
        for alias in item.get("aliases") or []:
            norm = normalize(str(alias))
            if norm:
                seen.add(norm)
    extras = []
    for answer in hand_answers:
        names = [answer.get("name") or "", *(answer.get("aliases") or [])]
        norms = [normalize(name) for name in names]
        if any(norm and norm in seen for norm in norms):
            continue
        label = (answer.get("name") or "").strip()
        if not label:
            continue
        extras.append(
            {
                "qid": None,
                "wiki": label,
                "label": label,
                "aliases": list(answer.get("aliases") or []),
                "sitelinks": 1,
                "rank": 10000 + len(extras),
            }
        )
    return extras


def harvest(only: list[str] | None = None) -> int:
    wanted = set(only or [])
    hand = {prompt["id"]: prompt for prompt in load_curated()}
    ACCEPTED.mkdir(parents=True, exist_ok=True)
    made = 0
    for spec in HARVEST:
        if wanted and spec["id"] not in wanted:
            continue
        base = hand.get(spec["id"])
        if not base:
            print(f"skip {spec['id']}: no hand prompt")
            continue
        print(f"[curated] {spec['id']} {base['text']}", flush=True)
        job = {
            "id": spec["id"],
            "text": base["text"],
            "category": base.get("category") or "general",
            "source": "curated",
            "must": spec["must"],
            "ban": spec.get("ban") or ["list of"],
            "min_links": 1,
            "min_answers": spec.get("min_answers", 30),
            "drop_binomial": bool(spec.get("drop_binomial")),
        }
        if spec.get("cap"):
            job["cap"] = spec["cap"]
        items = collect_categories(
            spec["categories"],
            ban=job["ban"],
            follow_geo=bool(spec.get("follow_geo")),
            follow_subcats=bool(spec.get("follow_subcats", True)),
            subcat_below=int(spec.get("subcat_below") or 80),
        )
        if len(items) < 40:
            print(f"  keep hand list: only {len(items)} category pages", flush=True)
            continue
        items = enrich_entities(items)
        blob = "\n".join(
            f"{item.get('label') or ''} {item.get('wiki') or ''}" for item in items
        ).lower()
        missing = [name for name in spec["must"] if name.lower() not in blob]
        if missing:
            print(f"  keep hand list: missing {', '.join(missing)}", flush=True)
            continue
        extras = missing_hand_items(items, base["answers"])
        if extras:
            print(f"  fold {len(extras)} hand-only answers", flush=True)
            items = [*items, *extras]
            job = {**job, "must": []}
        prompt, reason = build_prompt(job, items)
        if not prompt:
            print(f"  keep hand list: {reason}", flush=True)
            continue
        path = ACCEPTED / f"{prompt['id']}.json"
        path.write_text(json.dumps(prompt, ensure_ascii=False, indent=2) + "\n")
        made += 1
        print(f"  ok n={len(prompt['answers'])} (hand was {len(base['answers'])})", flush=True)
    print(f"curated prompts expanded: {made}", flush=True)
    return made
