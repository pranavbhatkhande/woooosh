"""Collect a notable answer pool, then load Wikidata sitelinks and aliases."""

from __future__ import annotations

from pipeline.clean import junk_title
from pipeline.net import request_json

WIKI = "https://en.wikipedia.org/w/api.php"
WD = "https://www.wikidata.org/w/api.php"
SPARQL = "https://query.wikidata.org/sparql"


def search_category(category: str, limit: int = 70) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    cont: dict = {}
    while len(found) < limit:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f'incategory:"{category}"',
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


def collect_categories(categories: list[str], limit: int, ban: list[str]) -> list[dict]:
    found: list[dict] = []
    seen: set[str] = set()
    for category in categories:
        for row in search_category(category, limit=limit):
            if row["qid"] in seen or junk_title(row["wiki"], ban):
                continue
            seen.add(row["qid"])
            found.append(row)
    return found
