"""Optional English Wikipedia pageview totals for gem and rarity tuning."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from urllib.parse import quote

import requests

from pipeline.http_client import USER_AGENT
from pipeline.paths import PAGEVIEW_CACHE
from pipeline.wikidata import SparqlError


def month_window(today: date | None = None) -> tuple[str, str]:
    today = today or date.today()
    end = today.replace(day=1)
    start = date(end.year - 1, end.month, 1)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def views_for_qids(client, qids: list[str]) -> dict[str, int]:
    titles = _enwiki_titles(client, qids)
    totals = {}
    start, end = month_window()
    cache = Path(PAGEVIEW_CACHE)
    cache.mkdir(parents=True, exist_ok=True)
    for qid, title in titles.items():
        totals[qid] = _views(client, title, start, end, cache)
    return totals


def _enwiki_titles(client, qids: list[str]) -> dict[str, str]:
    found = {}
    for start in range(0, len(qids), 40):
        chunk = qids[start : start + 40]
        values = " ".join(f"wd:{qid}" for qid in chunk)
        sparql = f"""
SELECT ?item ?title WHERE {{
  VALUES ?item {{ {values} }}
  ?article schema:about ?item .
  ?article schema:isPartOf <https://en.wikipedia.org/> .
  ?article schema:name ?title .
}}
"""
        try:
            rows = client.query(sparql)
        except SparqlError:
            continue
        for row in rows:
            qid = row["item"]["value"].rsplit("/", 1)[-1]
            title = row.get("title", {}).get("value", "")
            if title and qid not in found:
                found[qid] = title
    return found


def _views(client, title: str, start: str, end: str, cache: Path) -> int:
    key = hashlib.sha256(f"{title}|{start}|{end}".encode("utf-8")).hexdigest()
    path = cache / f"{key}.json"
    if path.exists():
        return int(json.loads(path.read_text(encoding="utf-8")))
    safe = quote(title.replace(" ", "_"), safe="")
    url = (
        "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
        f"en.wikipedia/all-access/user/{safe}/monthly/{start}/{end}"
    )
    client.http.wait()
    try:
        response = client.http.session.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}, timeout=(8, 30))
    except requests.RequestException:
        return 0
    total = 0
    if response.status_code == 200:
        for item in response.json().get("items", []):
            total += int(item.get("views") or 0)
    path.write_text(json.dumps(total), encoding="utf-8")
    return total
