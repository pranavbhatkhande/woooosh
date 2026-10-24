"""Drop answers that are not things a player would name."""

from __future__ import annotations

from pipeline.clean import junk_title


def scrub_prompt(prompt: dict) -> dict:
    kept = []
    for answer in prompt.get("answers") or []:
        name = (answer.get("name") or "").strip()
        if not name or junk_title(name):
            continue
        aliases = []
        for alias in answer.get("aliases") or []:
            text = (alias or "").strip()
            if text and not junk_title(text):
                aliases.append(text)
        kept.append({**answer, "name": name, "aliases": aliases})
    return {**prompt, "answers": kept}
