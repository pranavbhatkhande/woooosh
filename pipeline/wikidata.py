"""SPARQL client for query.wikidata.org. Cached, rate-limited, and retrying."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import requests

from pipeline.http_client import USER_AGENT, PoliteHttp
from pipeline.paths import SPARKQL_CACHE

ENDPOINT = "https://query.wikidata.org/sparql"


class SparqlError(RuntimeError):
    pass


class WikidataClient:
    def __init__(self, http: PoliteHttp | None = None, cache_dir: Path = SPARKQL_CACHE):
        self.http = http or PoliteHttp()
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def query(self, sparql: str) -> list[dict]:
        key = hashlib.sha256(sparql.encode("utf-8")).hexdigest()
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        payload = self._fetch(sparql)
        rows = payload.get("results", {}).get("bindings", [])
        path.write_text(json.dumps(rows), encoding="utf-8")
        return rows

    def _fetch(self, sparql: str) -> dict:
        last_error = "unknown"
        for attempt in range(4):
            self.http.wait()
            try:
                response = self.http.session.post(
                    ENDPOINT,
                    data=sparql.encode("utf-8"),
                    headers={
                        "Accept": "application/sparql-results+json",
                        "Content-Type": "application/sparql-query",
                        "User-Agent": USER_AGENT,
                    },
                    timeout=(8, 50),
                )
            except requests.RequestException as exc:
                last_error = type(exc).__name__
                self.http.after_backoff(8 * (attempt + 1))
                continue
            if response.status_code == 200 and response.text.lstrip().startswith("{"):
                return response.json()
            last_error = f"HTTP {response.status_code}"
            self.http.after_backoff(8 * (attempt + 1))
        raise SparqlError(last_error)


def alias_query(qids: list[str]) -> str:
    values = " ".join(f"wd:{qid}" for qid in qids)
    return f"""
SELECT ?item ?alias WHERE {{
  VALUES ?item {{ {values} }}
  ?item skos:altLabel ?alias .
  FILTER(LANG(?alias) = "en")
}}
"""


def group_aliases(rows: list[dict]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for row in rows:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        alias = row.get("alias", {}).get("value", "").strip()
        if alias:
            grouped.setdefault(qid, []).append(alias)
    return grouped
