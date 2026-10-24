"""Human review of the merged bank."""

from __future__ import annotations

from collections import Counter

from pipeline.publish import collect
from pipeline.tiering import TIER_IDS


def run_report(sample: int = 8, prompt_id: str = "") -> int:
    prompts, problems = collect()
    print(f"{len(prompts)} prompts pass quality gates. {len(problems)} would be dropped.")
    counts = Counter(prompt.get("source") or "?" for prompt in prompts)
    categories = Counter(prompt.get("category") or "?" for prompt in prompts)
    print("sources:", ", ".join(f"{key}={value}" for key, value in sorted(counts.items())))
    print("categories:", ", ".join(f"{key}={value}" for key, value in sorted(categories.items())))
    chosen = prompts
    if prompt_id:
        chosen = [prompt for prompt in prompts if prompt["id"] == prompt_id]
        if not chosen:
            print(f"No passing prompt with id {prompt_id}")
            return 1
    else:
        step = max(1, len(prompts) // max(sample, 1))
        chosen = prompts[::step][:sample]
    for prompt in chosen:
        _print_prompt(prompt)
    if problems:
        print("\nDropped:")
        for dropped_id, issues in problems[:15]:
            print(f"  {dropped_id}: {', '.join(issues)}")
    return 0


def _print_prompt(prompt: dict) -> None:
    answers = prompt.get("answers") or []
    hist = Counter(answer.get("tier") for answer in answers)
    gem = next((answer["name"] for answer in answers if answer.get("gem")), "?")
    print(f"\n{prompt['id']}  [{prompt.get('source')}]  {prompt.get('text')}")
    print(f"  {len(answers)} answers  gem={gem}")
    print("  " + "  ".join(f"{tier}:{hist.get(tier, 0)}" for tier in TIER_IDS))
    for tier in TIER_IDS:
        example = next((answer["name"] for answer in answers if answer.get("tier") == tier), "")
        if example:
            print(f"    {tier}: {example}")
