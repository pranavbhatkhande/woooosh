"""Print a review sample: the gem, and one answer from each other tier."""

from __future__ import annotations

from pipeline.clean import junk_title
from pipeline.publish import load_accepted, load_published
from pipeline.curated_loader import load_curated
from pipeline.tiers import TIER_ORDER


def _bank() -> list[dict]:
    published = load_published()
    if published:
        return [published[key] for key in sorted(published)]
    merged = dict(load_accepted())
    for prompt in load_curated():
        merged[prompt["id"]] = prompt
    return [merged[key] for key in sorted(merged)]


def _example(prompt: dict, tier: str) -> str:
    for answer in prompt.get("answers") or []:
        if answer.get("tier") == tier:
            return answer.get("name") or ""
    return "—"


def run_report(count: int = 8) -> None:
    prompts = _bank()
    if not prompts:
        print("no prompts yet. run wikidata or publish first.")
        return
    print(f"{len(prompts)} prompts\n")
    step = max(1, len(prompts) // max(1, count))
    shown = prompts[::step][:count]
    for prompt in shown:
        gem = next((answer["name"] for answer in prompt["answers"] if answer.get("gem")), "?")
        print(f"{prompt['id']}  [{prompt.get('source')}]  n={len(prompt['answers'])}")
        print(f"  {prompt['text']}")
        print(f"  gem: {gem}")
        others = ", ".join(f"{tier}={_example(prompt, tier)}" for tier in TIER_ORDER if tier != "escape")
        print(f"  {others}\n")
    suspects = []
    for prompt in prompts:
        gem = next((answer for answer in prompt["answers"] if answer.get("gem")), None)
        if gem and junk_title(gem.get("name") or ""):
            suspects.append(f"{prompt['id']}: gem {gem['name']}")
    if suspects:
        print("suspect gems:")
        for line in suspects:
            print(f"  {line}")
    else:
        print("no gem matched the junk filter")
