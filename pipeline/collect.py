"""Collect an exhaustive answer pool, then load Wikidata sitelinks and aliases.

Category prompts use every main-namespace page in the English Wikipedia
category, following continuation. A category with fewer than 80 direct pages
also walks subcategories, so "Types of cheese" still reaches the cheeses.
"""

from __future__ import annotations

import time

from pipeline.clean import junk_title
from pipeline.net import request_json

WIKI = "https://en.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"
SPARQL = "https://query.wikidata.org/sparql"
PAGE_CAP = 8000
DIRECT_ENOUGH = 80
SUB_DEPTH = 2

# Subcategories that are indexes, people, or geography dumps rather than answers.
_BAD_SUB = (
    "stub",
    "lists of",
    "list of",
    " by country",
    " by continent",
    " by year",
    "industry",
    " in culture",
    "people",
    "biograph",
    "template",
    "works about",
    "companies",
    "retailers",
    "players",
    "matches",
    "seasons",
    "managers",
    "non-playing",
    "directors",
    "chairmen",
    "squads",
    "supporters",
    "staff",
    "home grounds",
    "dishes",
    "navigational",
    "neighborhood",
    "metropolitan",
    "census-designated",
    "unincorporated",
    "ghost town",
    "images of",
    "photographs",
)


def category_title(name: str) -> str:
    text = (name or "").strip()
    if text.lower().startswith("category:"):
        return text
    return f"Category:{text}"


_GEO_SUB = (" by country", " by continent", " by year")


def bad_subcategory(title: str, *, follow_geo: bool = False) -> bool:
    low = category_title(title)[9:].lower()
    needles = _BAD_SUB
    if follow_geo:
        needles = tuple(needle for needle in _BAD_SUB if needle not in _GEO_SUB)
    return any(needle in low for needle in needles)


def search_category(category: str, limit: int = 70, *, deep: bool = False) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    cont: dict = {}
    while len(found) < limit:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f'{"deepcat" if deep else "incategory"}:"{category}"',
            "gsrnamespace": "0",
            "gsrlimit": "50",
            "gsrsort": "incoming_links_desc",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "maxlag": "5",
        }
        params.update(cont)
        try:
            data = request_json(WIKI, data=params, bucket="wiki", gap_key="wiki", timeout=30)
        except Exception as exc:
            print(f"  wiki failed for {category}: {exc}", flush=True)
            break
        if data.get("error"):
            print(f"  wiki error {category}: {data['error'].get('code')}", flush=True)
            break
        pages = (data.get("query") or {}).get("pages") or {}
        ordered = sorted(pages.values(), key=lambda page: page.get("index", 0))
        if not ordered:
            break
        for page in ordered:
            if page.get("ns", 0) != 0:
                continue
            title = page.get("title") or ""
            qid = (page.get("pageprops") or {}).get("wikibase_item")
            if not qid or qid in seen:
                continue
            seen.add(qid)
            found.append({"qid": qid, "wiki": title, "rank": len(found)})
            if len(found) >= limit:
                break
        cont = data.get("continue") or {}
        if not cont:
            break
    return found


def sparql_items(query: str) -> list[dict]:
    data = request_json(
        SPARQL,
        data={"query": query},
        bucket="sparql",
        gap_key="sparql",
        timeout=28,
    )
    rows = []
    seen = set()
    for binding in data.get("results", {}).get("bindings", []):
        uri = binding.get("item", {}).get("value", "")
        qid = uri.rsplit("/", 1)[-1]
        if not qid or qid in seen:
            continue
        seen.add(qid)
        label = binding.get("itemLabel", {}).get("value") or ""
        if label.startswith("Q") and label[1:].isdigit():
            label = ""
        try:
            links = int(float(binding.get("sitelinks", {}).get("value") or 0))
        except ValueError:
            links = 0
        rows.append({"qid": qid, "wiki": label, "label": label, "sitelinks": links, "rank": len(rows)})
    return rows


def enrich_sitelinks(items: list[dict]) -> list[dict]:
    missing = [item for item in items if item.get("sitelinks") is None]
    if not missing:
        return items
    by_qid = {item["qid"]: item for item in items}
    qids = [item["qid"] for item in missing]
    for start in range(0, len(qids), 40):
        chunk = qids[start : start + 40]
        values = " ".join(f"wd:{qid}" for qid in chunk)
        query = f"""
        SELECT ?item ?itemLabel ?sitelinks WHERE {{
          VALUES ?item {{ {values} }}
          OPTIONAL {{ ?item wikibase:sitelinks ?sitelinks }}
          OPTIONAL {{ ?item rdfs:label ?itemLabel FILTER(LANG(?itemLabel)="en") }}
        }}
        """
        try:
            data = request_json(
                SPARQL,
                data={"query": query},
                bucket="sparql",
                gap_key="sparql",
                timeout=35,
            )
        except Exception as exc:
            print(f"  sitelink lookup failed: {exc}", flush=True)
            continue
        for binding in data.get("results", {}).get("bindings", []):
            qid = binding.get("item", {}).get("value", "").rsplit("/", 1)[-1]
            item = by_qid.get(qid)
            if not item:
                continue
            label = binding.get("itemLabel", {}).get("value") or ""
            if label and not (label.startswith("Q") and label[1:].isdigit()):
                item["label"] = label
            raw = binding.get("sitelinks", {}).get("value")
            if raw is not None:
                try:
                    item["sitelinks"] = int(float(raw))
                except ValueError:
                    pass
    for item in items:
        if item.get("sitelinks") is None:
            item["sitelinks"] = max(1, 80 - int(item.get("rank") or 0))
        if not item.get("label"):
            item["label"] = item.get("wiki") or ""
    return items


def attach_aliases(items: list[dict]) -> list[dict]:
    by_qid = {item["qid"]: item for item in items if item.get("qid")}
    for item in by_qid.values():
        item.setdefault("aliases", [])
    qids = list(by_qid)
    for start in range(0, len(qids), 40):
        chunk = qids[start : start + 40]
        params = {
            "action": "wbgetentities",
            "format": "json",
            "props": "aliases",
            "languages": "en",
            "ids": "|".join(chunk),
        }
        try:
            data = request_json(WD, data=params, bucket="alias", gap_key="wd", timeout=30)
        except Exception as exc:
            print(f"  alias lookup failed: {exc}", flush=True)
            continue
        for qid, entity in (data.get("entities") or {}).items():
            item = by_qid.get(qid)
            if not item:
                continue
            for alias in (entity.get("aliases") or {}).get("en") or []:
                value = (alias.get("value") or "").strip()
                if value:
                    item["aliases"].append(value)
    return items


def _wiki_query(params: dict) -> dict | None:
    for _ in range(4):
        try:
            data = request_json(WIKI, data=params, bucket="wiki", gap_key="wiki", timeout=40)
        except Exception as exc:
            print(f"  wiki failed: {exc}", flush=True)
            return None
        code = (data.get("error") or {}).get("code")
        if code == "maxlag":
            time.sleep(5)
            continue
        if code:
            print(f"  wiki error {code}", flush=True)
            return None
        return data
    return None


def category_pages(category: str) -> list[dict]:
    """Every main-namespace page in the category, with a Wikidata id when one exists."""
    title = category_title(category)
    found: list[dict] = []
    seen: set[str] = set()
    cont: dict = {}
    while len(found) < PAGE_CAP:
        params = {
            "action": "query",
            "format": "json",
            "generator": "categorymembers",
            "gcmtitle": title,
            "gcmtype": "page",
            "gcmnamespace": "0",
            "gcmlimit": "500",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "maxlag": "5",
        }
        params.update(cont)
        data = _wiki_query(params)
        if not data:
            break
        pages = (data.get("query") or {}).get("pages") or {}
        if not pages:
            break
        for page in pages.values():
            wiki = page.get("title") or ""
            if not wiki or wiki in seen or page.get("ns", 0) != 0:
                continue
            seen.add(wiki)
            qid = (page.get("pageprops") or {}).get("wikibase_item")
            found.append({"qid": qid, "wiki": wiki})
            if len(found) >= PAGE_CAP:
                break
        cont = data.get("continue") or {}
        if not cont:
            break
    if len(found) >= PAGE_CAP:
        print(f"  {title}: stopped at page cap {PAGE_CAP}", flush=True)
    return found


def category_subcats(category: str) -> list[str]:
    title = category_title(category)
    found: list[str] = []
    cont: dict = {}
    while len(found) < 200:
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": title,
            "cmtype": "subcat",
            "cmlimit": "500",
            "maxlag": "5",
        }
        params.update(cont)
        data = _wiki_query(params)
        if not data:
            break
        members = (data.get("query") or {}).get("categorymembers") or []
        if not members:
            break
        for member in members:
            name = member.get("title") or ""
            if name:
                found.append(name)
        cont = data.get("continue") or {}
        if not cont:
            break
    return found


def place_answer_category(title: str) -> bool:
    """True when a subcategory title is itself a place, not an index."""
    name = category_title(title)[9:].lower()
    blocked = (
        " by ",
        "cities",
        "city in",
        "former",
        "histor",
        "econom",
        "tourist",
        "transport",
        "categor",
        "list of",
        "people",
        "building",
        "school",
        "mayor",
        "government",
        "timeline",
    )
    return not any(token in name for token in blocked)


def resolve_qids(items: list[dict]) -> list[dict]:
    """Fill Wikidata ids for rows that only have a Wikipedia title."""
    missing = [item for item in items if item.get("wiki") and not item.get("qid")]
    by_title = {item["wiki"]: item for item in missing}
    titles = list(by_title)
    for start in range(0, len(titles), 50):
        chunk = titles[start : start + 50]
        params = {
            "action": "query",
            "format": "json",
            "titles": "|".join(chunk),
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "redirects": "1",
            "maxlag": "5",
        }
        data = _wiki_query(params)
        if not data:
            continue
        pages = (data.get("query") or {}).get("pages") or {}
        for page in pages.values():
            wiki = page.get("title") or ""
            qid = (page.get("pageprops") or {}).get("wikibase_item")
            item = by_title.get(wiki)
            if item is None:
                # redirects: the query title may differ from the normalized title
                continue
            if qid:
                item["qid"] = qid
        for redirect in (data.get("query") or {}).get("redirects") or []:
            src = redirect.get("from") or ""
            dst = redirect.get("to") or ""
            item = by_title.get(src)
            if not item:
                continue
            for page in pages.values():
                if page.get("title") == dst:
                    qid = (page.get("pageprops") or {}).get("wikibase_item")
                    if qid:
                        item["qid"] = qid
    return items


def collect_categories(
    categories: list[str],
    ban: list[str] | None = None,
    limit: int | None = None,
    follow_geo: bool = False,
    follow_subcats: bool = False,
    subcat_below: int = DIRECT_ENOUGH,
    places_from_subcats: bool = False,
) -> list[dict]:
    """Exhaustive union of categories. Subcategories are walked only when asked."""
    cap = int(limit) if limit else PAGE_CAP
    found: list[dict] = []
    seen: set[str] = set()
    seen_cat: set[str] = set()
    queue: list[tuple[str, int]] = [(category_title(category), 0) for category in categories]
    while queue and len(found) < cap:
        title, depth = queue.pop(0)
        key = title.lower()
        if key in seen_cat:
            continue
        seen_cat.add(key)
        pages = category_pages(title)
        print(f"  {title}: {len(pages)} pages", flush=True)
        for page in pages:
            if len(found) >= cap:
                break
            wiki = page["wiki"]
            if junk_title(wiki, ban):
                continue
            dedupe = page.get("qid") or wiki.lower()
            if dedupe in seen:
                continue
            seen.add(dedupe)
            found.append({"qid": page.get("qid"), "wiki": wiki, "rank": len(found), "sitelinks": None})
        if places_from_subcats and len(pages) < subcat_below:
            for sub in category_subcats(title):
                if not place_answer_category(sub):
                    continue
                name = category_title(sub)[9:]
                if not name or junk_title(name, ban):
                    continue
                dedupe = name.lower()
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                found.append({"qid": None, "wiki": name, "rank": len(found), "sitelinks": None})
        elif follow_subcats and depth < SUB_DEPTH and len(pages) < subcat_below:
            for sub in category_subcats(title):
                if bad_subcategory(sub, follow_geo=follow_geo):
                    continue
                queue.append((sub, depth + 1))
    if places_from_subcats:
        resolve_qids(found)
    return found


def enrich_entities(items: list[dict]) -> list[dict]:
    """Fill English label, alias list, and sitelink count in one Wikidata call per chunk."""
    by_qid = {item["qid"]: item for item in items if item.get("qid")}
    for item in items:
        item.setdefault("aliases", [])
    qids = list(by_qid)
    for start in range(0, len(qids), 50):
        chunk = qids[start : start + 50]
        params = {
            "action": "wbgetentities",
            "format": "json",
            "props": "labels|aliases|sitelinks",
            "languages": "en",
            "ids": "|".join(chunk),
        }
        try:
            data = request_json(WD, data=params, bucket="entity", gap_key="wd", timeout=40)
        except Exception as exc:
            print(f"  entity lookup failed: {exc}", flush=True)
            continue
        for qid, entity in (data.get("entities") or {}).items():
            item = by_qid.get(qid)
            if not item or not isinstance(entity, dict):
                continue
            label = ((entity.get("labels") or {}).get("en") or {}).get("value") or ""
            if label and not (label.startswith("Q") and label[1:].isdigit()):
                item["label"] = label
            links = entity.get("sitelinks") or {}
            if isinstance(links, dict) and links:
                item["sitelinks"] = len(links)
            aliases = []
            for alias in (entity.get("aliases") or {}).get("en") or []:
                value = (alias.get("value") or "").strip()
                if value and value not in aliases:
                    aliases.append(value)
            item["aliases"] = aliases[:6]
    for item in items:
        if item.get("sitelinks") is None:
            item["sitelinks"] = 1
        if not item.get("label"):
            item["label"] = item.get("wiki") or ""
        item.setdefault("aliases", [])
    return items
