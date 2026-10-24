"""Fill open American prompts out to the real set, then pin the hand-list order.

Closed sets (NFL, NBA, MLB, capitals, holidays) are not expanded. Their hand
lists are already the whole answer key.
"""

from __future__ import annotations

import json

from pipeline.collect import (
    category_subcats,
    category_title,
    collect_categories,
    enrich_entities,
    place_answer_category,
    search_category,
)
from pipeline.curated_loader import _entries
from pipeline.curated_us import US
from pipeline.make_prompt import build_prompt
from pipeline.net import CACHE, request_json
from pipeline.quality import publishable
from pipeline.audience import pin_hand_order
from pipeline.collect import SPARQL

ACCEPTED = CACHE / "accepted"
# Classes that are people and creatures, not planets, ships, or spells.
_CHARACTER = " ".join(
    [
        "wd:Q95074",
        "wd:Q15773347",
        "wd:Q15711870",
        "wd:Q1569167",
        "wd:Q15773317",
        "wd:Q80447738",
        "wd:Q386208",
        "wd:Q15632617",
        "wd:Q87576284",
        "wd:Q1114461",
        "wd:Q3658341",
        "wd:Q3375722",
    ]
)

# These hand lists are the entire closed set. Do not harvest a larger category.
CLOSED = frozenset({"cur-nfl", "cur-nba", "cur-mlb", "cur-capital", "cur-holiday"})

SPECS = [
    {
        "id": "cur-pokemon",
        "min_links": 0,
        "cap": 1800,
        "where": "?item wdt:P1685 ?dex .",
        "optional_links": True,
        "ban": ["list of", "pokédex", "pokedex", "index"],
    },
    {
        "id": "cur-starwars",
        "min_links": 1,
        "cap": 1800,
        "where": f"?item wdt:P1080 wd:Q19786052 . ?item wdt:P31 ?class . VALUES ?class {{ {_CHARACTER} wd:Q33125444 wd:Q28020127 wd:Q89050960 }}",
        "ban": ["list of", "universe", "episode", "soundtrack"],
    },
    {
        "id": "cur-potter",
        "min_links": 1,
        "cap": 1800,
        "where": f"?item wdt:P1080 wd:Q5410773 . ?item wdt:P31 ?class . VALUES ?class {{ {_CHARACTER} wd:Q15298259 }}",
        "ban": ["list of", "spell", "subject", "family", "cottage", "school"],
    },
    {
        "id": "cur-simpsons",
        "min_links": 1,
        "cap": 1800,
        "where": f"?item wdt:P1080 wd:Q61468436 . ?item wdt:P31 ?class . VALUES ?class {{ {_CHARACTER} }}",
        "ban": ["list of", "episode", "burger", "universe"],
    },
    {
        "id": "cur-game-char",
        "min_links": 4,
        "cap": 1800,
        "where": "?item wdt:P31 wd:Q1569167 .",
        "ban": ["list of", "series", "franchise", "episode"],
    },
    {
        "id": "cur-animated",
        "min_links": 2,
        "cap": 1800,
        "where": "?item wdt:P31 wd:Q202866 . ?item wdt:P495 wd:Q30 .",
        "ban": ["list of", "soundtrack", "episode", "short"],
    },
    {
        "id": "cur-director",
        # Rank by the films they directed, not by how famous the person is.
        # A celebrity with one stray "director" occupation should not be taxi.
        "directors": True,
        "cap": 1800,
        "ban": ["list of"],
    },
    {
        "id": "cur-tv",
        "min_links": 10,
        "cap": 1800,
        "where": "?item wdt:P31 wd:Q5398426 . ?item wdt:P495 wd:Q30 .",
        "ban": ["list of", "episode", "season", "soundtrack"],
    },
    {
        "id": "cur-channel",
        "min_links": 2,
        "cap": 800,
        "where": "?item wdt:P31 wd:Q2001305 . ?item wdt:P17 wd:Q30 .",
        "ban": ["list of", "affiliate", "defunct"],
    },
    {
        "id": "cur-cereal",
        "categories": [
            "General Mills cereals",
            "Kellogg's cereals",
            "Nestlé cereals",
            "Post cereals",
            "Quaker Oats Company cereals",
            "Ralston cereals",
            "Weetabix cereals",
            "Breakfast cereals",
        ],
        "ban": ["list of", "company", "mascot"],
    },
    {
        "id": "cur-snack",
        "categories": [
            "Brand name snack foods",
            "Frito-Lay brands",
            "Brand name potato chips and crisps",
            "Brand name cookies",
            "Brand name crackers",
            "Popcorn brands",
            "Nabisco brands",
            "Hostess Brands brands",
        ],
        "ban": ["list of", "company", "factory"],
    },
    {
        "id": "cur-clothes-brand",
        "categories": ["Clothing brands of the United States"],
        "ban": ["list of"],
    },
    {
        "id": "cur-disney-char",
        # Animated characters who appear in a Walt Disney Animation, Pixar,
        # DisneyToon, or Disney Television Animation film. Cameo universes
        # (Star Wars, Marvel, Sonic, and the rest) stay out.
        "min_links": 0,
        "optional_links": True,
        "cap": 1800,
        "where": """
          ?work wdt:P31 wd:Q202866 .
          VALUES ?studio { wd:Q191224 wd:Q1047410 wd:Q2724393 wd:Q1227466 }
          ?work wdt:P272 ?studio .
          ?item wdt:P1441 ?work .
          ?item wdt:P31 wd:Q15711870 .
          FILTER NOT EXISTS {
            ?item wdt:P1080 ?universe .
            VALUES ?universe {
              wd:Q19786052 wd:Q5410773 wd:Q61468436 wd:Q931597 wd:Q1152150
              wd:Q20203549 wd:Q50917996
            }
          }
        """,
        "ban": ["list of", "soundtrack", "episode"],
    },
    {"id": "cur-city-ca", "cities": True, "ban": ["list of"]},
]


def _rows(bindings: list[dict]) -> list[dict]:
    items = []
    seen: set[str] = set()
    for binding in bindings:
        qid = binding["item"]["value"].rsplit("/", 1)[-1]
        if qid in seen:
            continue
        seen.add(qid)
        label = binding.get("itemLabel", {}).get("value") or ""
        if not label or (label.startswith("Q") and label[1:].isdigit()):
            continue
        raw = binding.get("sitelinks", {}).get("value")
        try:
            links = int(float(raw)) if raw else 0
        except ValueError:
            links = 0
        items.append({"qid": qid, "wiki": label, "label": label, "sitelinks": links, "aliases": []})
    return items


def fetch_sparql(where: str, *, min_links: int, optional_links: bool) -> list[dict]:
    if optional_links:
        link = "OPTIONAL { ?item wikibase:sitelinks ?sitelinks }"
        floor = ""
    else:
        link = "?item wikibase:sitelinks ?sitelinks ."
        floor = f"FILTER(?sitelinks >= {int(min_links)})"
    query = f"""
    SELECT ?item ?itemLabel ?sitelinks WHERE {{
      {where}
      {link}
      ?item rdfs:label ?itemLabel .
      FILTER(LANG(?itemLabel)="en")
      {floor}
    }}
    """
    data = request_json(SPARQL, data={"query": query}, bucket="sparql", gap_key="sparql", timeout=90)
    return _rows((data.get("results") or {}).get("bindings") or [])


def california_cities() -> list[dict]:
    items = []
    seen: set[str] = set()
    for sub in category_subcats("Incorporated cities and towns in California"):
        name = category_title(sub)[9:]
        if not name.endswith(", California"):
            continue
        if not place_answer_category(name):
            continue
        city = name[: -len(", California")].strip()
        key = city.lower()
        if not city or key in seen:
            continue
        seen.add(key)
        items.append({"qid": None, "wiki": city, "label": city, "sitelinks": 1, "aliases": [name]})
    return items


def director_items() -> list[dict]:
    """US citizens credited as director on a film, scored by those films' sitelinks."""
    query = """
    SELECT ?item ?itemLabel (SUM(?filmLinks) AS ?fame) WHERE {
      ?film wdt:P57 ?item .
      ?film wdt:P31 wd:Q11424 .
      ?item wdt:P27 wd:Q30 .
      ?film wikibase:sitelinks ?filmLinks .
      FILTER(?filmLinks >= 5)
      ?item rdfs:label ?itemLabel .
      FILTER(LANG(?itemLabel)="en")
    }
    GROUP BY ?item ?itemLabel
    """
    data = request_json(SPARQL, data={"query": query}, bucket="sparql", gap_key="sparql", timeout=90)
    items = []
    seen: set[str] = set()
    for binding in (data.get("results") or {}).get("bindings") or []:
        qid = binding["item"]["value"].rsplit("/", 1)[-1]
        if qid in seen:
            continue
        seen.add(qid)
        label = binding.get("itemLabel", {}).get("value") or ""
        if not label or (label.startswith("Q") and label[1:].isdigit()):
            continue
        try:
            fame = int(float(binding.get("fame", {}).get("value") or 0))
        except ValueError:
            fame = 0
        items.append({"qid": qid, "wiki": label, "label": label, "sitelinks": fame, "aliases": []})
    return items


def gather(spec: dict) -> list[dict]:
    if spec.get("cities"):
        return california_cities()
    if spec.get("directors"):
        return director_items()
    if spec.get("where"):
        return fetch_sparql(spec["where"], min_links=int(spec.get("min_links") or 1), optional_links=bool(spec.get("optional_links")))
    if spec.get("deepcat"):
        return search_category(spec["deepcat"], limit=int(spec.get("cap") or 1500), deep=True)
    items = collect_categories(spec.get("categories") or [], ban=spec.get("ban") or ["list of"], follow_subcats=False)
    return enrich_entities(items)


def _cap(items: list[dict], limit: int | None) -> list[dict]:
    if not limit or len(items) <= limit:
        return items
    ranked = sorted(items, key=lambda item: (-int(item.get("sitelinks") or 0), (item.get("label") or item.get("wiki") or "").lower()))
    return ranked[:limit]


def fill(only: list[str] | None = None) -> int:
    hand = {spec["id"]: spec for spec in US}
    wanted = set(only or [])
    ACCEPTED.mkdir(parents=True, exist_ok=True)
    made = 0
    for spec in SPECS:
        if wanted and spec["id"] not in wanted:
            continue
        if spec["id"] in CLOSED:
            continue
        base = hand.get(spec["id"])
        if not base:
            print(f"skip {spec['id']}: no hand list", flush=True)
            continue
        print(f"[fill] {spec['id']} {base['text']}", flush=True)
        try:
            items = gather(spec)
        except Exception as exc:
            print(f"  keep hand list: {type(exc).__name__}: {exc}", flush=True)
            continue
        items = _cap(items, spec.get("cap"))
        print(f"  gathered {len(items)}", flush=True)
        if len(items) < 40:
            print("  keep hand list: not a fuller set", flush=True)
            continue
        job = {
            "id": spec["id"],
            "text": base["text"],
            "category": base.get("category") or "general",
            "source": "curated",
            "must": [],
            "ban": spec.get("ban") or ["list of"],
            "min_links": 0,
            "min_answers": 30,
        }
        prompt, reason = build_prompt(job, items, retain_stats=True)
        if not prompt:
            print(f"  keep hand list: {reason}", flush=True)
            continue
        pinned = pin_hand_order(prompt, _entries(base["answers"]))
        cleaned, errors = publishable(pinned)
        if errors:
            print(f"  keep hand list: {errors[0]}", flush=True)
            continue
        path = ACCEPTED / f"{cleaned['id']}.json"
        path.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n")
        made += 1
        taxi = [answer["name"] for answer in cleaned["answers"] if answer["tier"] == "taxi"][:8]
        print(f"  ok n={len(cleaned['answers'])} taxi={taxi}", flush=True)
    print(f"filled prompts: {made}", flush=True)
    return made
