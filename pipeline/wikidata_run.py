"""Build Wikidata-backed prompts. Resumable: finished ids are skipped."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from pipeline.collect import collect_categories, enrich_entities, sparql_items
from pipeline.jobs import iter_jobs
from pipeline.make_prompt import build_prompt
from pipeline.net import CACHE

ACCEPTED = CACHE / "accepted"
FAILS = CACHE / "fails.json"
ROOT = Path(__file__).resolve().parents[1]
CAPS = {"film": 40, "game": 26, "album": 34, "tv": 22, "tvuk": 12}


def published_wd_ids() -> set[str]:
    """Ids already in the bank. Weekly runs skip these unless --only names them."""
    index = ROOT / "data" / "index.json"
    if not index.exists():
        return set()
    try:
        data = json.loads(index.read_text())
    except json.JSONDecodeError:
        return set()
    ids: set[str] = set()
    for shard in data.get("shards") or []:
        ids.update(shard.get("ids") or [])
    return {prompt_id for prompt_id in ids if prompt_id.startswith("wd-")}


def _load_fails() -> dict:
    if FAILS.exists():
        try:
            return json.loads(FAILS.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _save_fail(fails: dict, job_id: str, reason: str) -> None:
    fails[job_id] = reason
    FAILS.parent.mkdir(parents=True, exist_ok=True)
    FAILS.write_text(json.dumps(fails, indent=2, ensure_ascii=False))


def _counts(done: set[str], jobs_by_id: dict) -> Counter:
    counts: Counter = Counter()
    for job_id in done:
        job = jobs_by_id.get(job_id)
        if job:
            counts[job["kind"]] += 1
    return counts


def _gather(job: dict) -> tuple[list[dict] | None, str]:
    if job.get("mode") == "sparql":
        try:
            items = sparql_items(job["query"])
        except Exception as exc:
            return None, f"sparql {type(exc).__name__}: {exc}"
        if len(items) < 30:
            return None, f"sparql returned {len(items)}"
        items = enrich_entities(items)
        return items, ""
    items = collect_categories(
        job.get("categories") or [],
        ban=job.get("ban") or [],
        follow_subcats=bool(job.get("follow_subcats")),
        subcat_below=int(job.get("subcat_below") or 80),
        places_from_subcats=bool(job.get("places_from_subcats")),
    )
    if len(items) < 30:
        return None, f"only {len(items)} category pages"
    items = enrich_entities(items)
    return items, ""


def _run_job(job: dict) -> tuple[dict | None, str]:
    items, reason = _gather(job)
    if items is None:
        return None, reason
    return build_prompt(job, items)


def generate(target: int = 210, only: list[str] | None = None, retry_failed: bool = False, refresh: bool = False) -> int:
    ACCEPTED.mkdir(parents=True, exist_ok=True)
    jobs = list(iter_jobs())
    by_id = {job["id"]: job for job in jobs}
    if only:
        wanted = set(only)
        jobs = [job for job in jobs if job["id"] in wanted]
        missing = wanted - {job["id"] for job in jobs}
        for job_id in missing:
            print(f"unknown job {job_id}")
    done: set[str] = set()
    if not refresh:
        done = {path.stem for path in ACCEPTED.glob("wd-*.json")}
        if not only:
            done |= published_wd_ids()
    fails = {} if retry_failed or refresh else _load_fails()
    counts = _counts(done, by_id)
    made = len(done)

    def consider(job: dict, honor_caps: bool) -> None:
        nonlocal made
        if not only and made >= target:
            return
        if job["id"] in done:
            return
        cap = CAPS.get(job["kind"])
        if honor_caps and cap and counts[job["kind"]] >= cap:
            return
        if job["id"] in fails:
            return
        print(f"[{made}/{target}] {job['id']} {job['text']}", flush=True)
        try:
            prompt, reason = _run_job(job)
        except Exception as exc:
            prompt, reason = None, f"{type(exc).__name__}: {exc}"
        if not prompt:
            print(f"  skip {reason}", flush=True)
            if refresh:
                stale = ACCEPTED / f"{job['id']}.json"
                if stale.exists():
                    stale.unlink()
            _save_fail(fails, job["id"], reason)
            return
        (ACCEPTED / f"{prompt['id']}.json").write_text(json.dumps(prompt, ensure_ascii=False, indent=2))
        done.add(prompt["id"])
        counts[job["kind"]] += 1
        made += 1
        gem = next(answer["name"] for answer in prompt["answers"] if answer["gem"])
        tiers = Counter(answer["tier"] for answer in prompt["answers"])
        print(f"  ok n={len(prompt['answers'])} gem={gem} {dict(tiers)}", flush=True)

    for job in jobs:
        consider(job, honor_caps=not bool(only))
    if not only and made < target:
        print(f"backfill toward {target}, currently {made}", flush=True)
        for job in jobs:
            if made >= target:
                break
            consider(job, honor_caps=False)
    print(f"wikidata prompts ready: {len(list(ACCEPTED.glob('wd-*.json')))}", flush=True)
    return made
