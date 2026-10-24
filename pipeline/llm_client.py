"""OpenAI-compatible chat client for a local Ollama model. Calls are cached."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import requests

from pipeline.paths import LLM_CACHE


class LlmError(RuntimeError):
    pass


class LlmClient:
    def __init__(self, url: str, model: str, timeout: int = 180, cache_dir: Path = LLM_CACHE):
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()

    def json_chat(self, messages: list[dict], *, temperature: float, max_tokens: int, purpose: str) -> dict:
        raw = self._complete(messages, temperature=temperature, max_tokens=max_tokens, purpose=purpose)
        return parse_json_object(raw)

    def _complete(self, messages: list[dict], *, temperature: float, max_tokens: int, purpose: str) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "purpose": purpose,
        }
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))["content"]
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "chat_template_kwargs": {"enable_thinking": False},
        }
        content = self._post(body)
        path.write_text(json.dumps({"content": content}), encoding="utf-8")
        return content

    def _post(self, body: dict) -> str:
        endpoint = f"{self.url}/chat/completions"
        response = self._send(endpoint, body)
        if response.status_code == 400:
            slim = {
                "model": body["model"],
                "messages": body["messages"],
                "temperature": body.get("temperature", 0.4),
                "max_tokens": body.get("max_tokens", 2048),
            }
            response = self._send(endpoint, slim)
        if response.status_code >= 400:
            raise LlmError(f"HTTP {response.status_code}: {response.text[:240]}")
        try:
            message = response.json()["choices"][0]["message"]
        except (KeyError, IndexError, ValueError) as exc:
            raise LlmError(f"bad completion payload: {exc}") from exc
        content = message.get("content") or ""
        if not content.strip():
            content = message.get("reasoning") or message.get("thinking") or ""
        if not str(content).strip():
            raise LlmError("empty completion")
        return str(content)

    def _send(self, endpoint: str, body: dict) -> requests.Response:
        try:
            return self.session.post(endpoint, json=body, timeout=self.timeout)
        except requests.RequestException as exc:
            raise LlmError(f"could not reach {endpoint}: {exc}") from exc


def parse_json_object(text: str) -> dict:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            raise LlmError("model did not return JSON")
        value = json.loads(cleaned[start : end + 1])
    if not isinstance(value, dict):
        raise LlmError("JSON root was not an object")
    return value
