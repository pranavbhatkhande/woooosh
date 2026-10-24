"""Polite HTTP for Wikidata and Wikipedia."""

from __future__ import annotations

import time

import requests

USER_AGENT = "WOOOOSHPipeline/1.0 (https://woooosh.ai)"


class PoliteHttp:
    def __init__(self, delay: float = 1.05, user_agent: str = USER_AGENT):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self._next = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        if now < self._next:
            time.sleep(self._next - now)
        self._next = time.monotonic() + self.delay

    def after_backoff(self, seconds: float) -> None:
        self._next = max(self._next, time.monotonic() + seconds)
