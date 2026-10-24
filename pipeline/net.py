"""Polite cached HTTP for Wikidata and Wikipedia."""

from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "pipeline" / "cache"
UA = "WooooshPromptPipeline/1.0 (https://github.com/pranavbhatkhande/woooosh)"

_LAST = {"wiki": 0.0, "sparql": 0.0, "wd": 0.0}
_GAP = {"wiki": 0.12, "sparql": 1.05, "wd": 0.25}


def _cache_path(bucket: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    folder = CACHE / bucket
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{digest}.json"


def request_json(url: str, *, data: dict | None = None, bucket: str, gap_key: str, timeout: int = 40, use_cache: bool = True) -> dict:
    key = url + "|" + json.dumps(data or {}, sort_keys=True)
    path = _cache_path(bucket, key)
    if use_cache and path.exists():
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            path.unlink(missing_ok=True)

    wait = _GAP[gap_key] - (time.time() - _LAST[gap_key])
    if wait > 0:
        time.sleep(wait)

    payload = None
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if data is not None:
        payload = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    attempt = 0
    while True:
        attempt += 1
        req = urllib.request.Request(url, data=payload, headers=headers)
        _LAST[gap_key] = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as res:
                body = json.loads(res.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code in {429, 503} and attempt < 5:
                retry = exc.headers.get("Retry-After") if exc.headers else None
                delay = float(retry) if retry and retry.isdigit() else min(60, 8 * attempt)
                print(f"  backoff {delay:.0f}s after HTTP {exc.code}", flush=True)
                time.sleep(delay)
                continue
            if exc.code in {500, 504} and attempt < 3:
                time.sleep(4 * attempt)
                continue
            raise
        except (TimeoutError, urllib.error.URLError):
            if attempt < 3:
                time.sleep(3 * attempt)
                continue
            raise
    if use_cache:
        path.write_text(json.dumps(body))
    return body
