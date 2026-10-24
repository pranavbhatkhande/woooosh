"""Build the Wikidata half of the bank. Safe to stop and run again."""

from __future__ import annotations

import json
import time
from pathlib import Path

from pipeline.assemble import assemble_prompt
from pipeline.http_client import PoliteHttp
from pipeline.paths import OUT_PROMPTS
from pipeline.templates import all_templates
from pipeline.wikidata import SparqlError, WikidataClient, alias_query, group_aliases


def generate_wikidata(limit: int = 0, refresh: bool = False, pageviews: bool = False, delay: float = 1.05, only: str = "") -> int:
    templates = all_templates()
    if only:
        wanted = {part.strip() for part in only.split(",") if part.strip()}
        templates = [template for template in templates if template.id in wanted or f"wd-{template.id}" in wanted]
    OUT_PROMPTS.mkdir(parents=True, exist_ok=True)
    client = WikidataClient(PoliteHttp(delay=delay))
    accepted = 0
    skipped = 0
    rejected = 0
    failed = 0
    started = time.time()
    print(f"Wikidata templates: {len(templates)}", flush=True)
    for index, template in enumerate(templates, start=1):
        path = OUT_PROMPTS / f"wd-{template.id}.json"
        if path.exists() and not refresh:
            skipped += 1
            continue
        if limit and accepted >= limit:
            break
        t0 = time.time()
        try:
            prompt, issues = _one(client, template, pageviews)
        except SparqlError as exc:
            failed += 1
            print(f"[{index}/{len(templates)}] FAIL {template.id}: {exc}", flush=True)
            continue
        except Exception as exc:  # keep a long run alive if one template is malformed
            failed += 1
            print(f"[{index}/{len(templates)}] ERROR {template.id}: {type(exc).__name__}: {exc}", flush=True)
            continue
        if prompt is None:
            rejected += 1
            _reject(template.id, issues)
            if refresh and path.exists():
                path.unlink()
            print(f"[{index}/{len(templates)}] SKIP {template.id}: {', '.join(issues)} ({time.time() - t0:.1f}s)", flush=True)
            continue
        path.write_text(json.dumps(prompt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        accepted += 1
        gem = next(answer["name"] for answer in prompt["answers"] if answer["gem"])
        print(
            f"[{index}/{len(templates)}] OK {prompt['id']} answers={len(prompt['answers'])} gem={gem} ({time.time() - t0:.1f}s)",
            flush=True,
        )
    elapsed = time.time() - started
    print(
        f"Done in {elapsed / 60:.1f} min. new={accepted} skipped={skipped} rejected={rejected} failed={failed}",
        flush=True,
    )
    return 0 if failed == 0 else 1


def _one(client: WikidataClient, template, pageviews: bool):
    rows = client.query(template.sparql)
    qids = []
    seen = set()
    for row in rows:
        qid = row.get("item", {}).get("value", "").rsplit("/", 1)[-1]
        if qid and qid not in seen:
            seen.add(qid)
            qids.append(qid)
    qids = qids[: template.limit]
    alias_map = _aliases(client, qids)
    views = _pageviews(client, qids) if pageviews and qids else None
    return assemble_prompt(template, rows, alias_map, views)


def _aliases(client: WikidataClient, qids: list[str]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = {}
    if not qids:
        return merged
    for start in range(0, len(qids), 40):
        chunk = qids[start : start + 40]
        try:
            rows = client.query(alias_query(chunk))
        except SparqlError as exc:
            print(f"  alias chunk failed ({exc}); continuing", flush=True)
            continue
        for qid, aliases in group_aliases(rows).items():
            merged.setdefault(qid, []).extend(aliases)
    return merged


def _pageviews(client: WikidataClient, qids: list[str]) -> dict[str, int]:
    """Optional English Wikipedia pageviews. Slow; off unless --pageviews is set."""
    from pipeline.pageviews import views_for_qids

    return views_for_qids(client, qids)


def _reject(identifier: str, issues: list[str]) -> None:
    path = Path(OUT_PROMPTS).parent / "rejected.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"id": f"wd-{identifier}", "issues": issues}) + "\n")
