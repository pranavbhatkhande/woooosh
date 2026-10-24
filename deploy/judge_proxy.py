#!/usr/bin/env python3
"""Token-checking reverse proxy in front of a local Ollama.

Bind is 127.0.0.1 only. Put Tailscale Funnel or a Cloudflare Tunnel on this
port, never on Ollama's own port. The proxy refuses every request that does
not present JUDGE_PROXY_TOKEN as a Bearer token.

  JUDGE_PROXY_TOKEN   required shared secret
  JUDGE_PROXY_BIND    default 127.0.0.1
  JUDGE_PROXY_PORT    default 11435
  OLLAMA_UPSTREAM     default http://127.0.0.1:11434
"""

from __future__ import annotations

import hmac
import json
import os
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BIND = os.environ.get("JUDGE_PROXY_BIND", "127.0.0.1")
PORT = int(os.environ.get("JUDGE_PROXY_PORT", "11435"))
UPSTREAM = os.environ.get("OLLAMA_UPSTREAM", "http://127.0.0.1:11434").rstrip("/")
TOKEN = os.environ.get("JUDGE_PROXY_TOKEN", "")
MAX_BODY = 65_536
WINDOW = 60.0
LIMIT = 60
ALLOWED = {"/v1/chat/completions", "/api/chat"}

_hits: list[float] = []


def _authorized(header: str) -> bool:
    if not TOKEN or not header.startswith("Bearer "):
        return False
    given = header[7:].strip()
    return hmac.compare_digest(given, TOKEN)


def _allowed() -> bool:
    now = time.monotonic()
    fresh = [stamp for stamp in _hits if now - stamp < WINDOW]
    _hits[:] = fresh
    if len(_hits) >= LIMIT:
        return False
    _hits.append(now)
    return True


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] != "/healthz":
            self._send(404, b'{"error":"not found"}\n', "application/json")
            return
        self._send(200, b'{"ok":true}\n', "application/json")

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path not in ALLOWED:
            self._send(404, b'{"error":"not found"}\n', "application/json")
            return
        if not _authorized(self.headers.get("Authorization", "")):
            self._send(401, b'{"error":"unauthorized"}\n', "application/json")
            return
        if not _allowed():
            self._send(429, b'{"error":"rate"}\n', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            self._send(413, b'{"error":"body"}\n', "application/json")
            return
        payload = self.rfile.read(length)
        request = urllib.request.Request(
            UPSTREAM + path,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read()
                kind = response.headers.get("Content-Type", "application/json")
                self._send(response.status, data, kind)
        except urllib.error.HTTPError as exc:
            data = exc.read()
            self._send(exc.code, data or b'{"error":"upstream"}\n', "application/json")
        except Exception:
            self._send(502, b'{"error":"upstream"}\n', "application/json")


def main() -> int:
    if not TOKEN:
        print("JUDGE_PROXY_TOKEN is required. Refusing to expose Ollama without a secret.", file=sys.stderr)
        return 1
    if BIND not in {"127.0.0.1", "::1", "localhost"}:
        print(f"refusing to bind {BIND}. Keep the proxy on localhost and tunnel that.", file=sys.stderr)
        return 1
    server = ThreadingHTTPServer((BIND, PORT), Handler)
    print(f"judge proxy on http://{BIND}:{PORT} -> {UPSTREAM}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
