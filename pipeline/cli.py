"""Command line for the offline prompt bank.

    python -m pipeline wikidata
    python -m pipeline llm --count 25
    python -m pipeline report
    python -m pipeline publish
"""

from __future__ import annotations

import argparse
import os


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m pipeline", description="Build and publish the WOOOOSH prompt bank.")
    sub = parser.add_subparsers(dest="command", required=True)

    wikidata = sub.add_parser("wikidata", help="Generate prompts from Wikidata templates.")
    wikidata.add_argument("--limit", type=int, default=0, help="Stop after this many newly accepted prompts. 0 runs every template.")
    wikidata.add_argument("--refresh", action="store_true", help="Rebuild prompts even if an output file exists.")
    wikidata.add_argument("--pageviews", action="store_true", help="Blend English Wikipedia pageviews into rarity. Slow.")
    wikidata.add_argument("--delay", type=float, default=1.05, help="Seconds between network calls.")
    wikidata.add_argument("--only", default="", help="Comma-separated template ids to run.")

    llm = sub.add_parser("llm", help="Generate prompts with a local OpenAI-compatible model.")
    llm.add_argument("--count", type=int, default=25, help="How many new prompts to accept.")
    llm.add_argument("--url", default=os.environ.get("WOOOOSH_LLM_URL", "http://localhost:11434/v1"))
    llm.add_argument("--model", default=os.environ.get("WOOOOSH_LLM_MODEL", "qwen3.8:27b"))
    llm.add_argument("--timeout", type=int, default=180)
    llm.add_argument("--refresh", action="store_true")

    report = sub.add_parser("report", help="Print sample prompts for review.")
    report.add_argument("--sample", type=int, default=8)
    report.add_argument("--id", default="", help="Print one prompt id.")

    publish = sub.add_parser("publish", help="Write data shards, the index, and the daily schedule.")
    publish.add_argument("--days", type=int, default=450, help="How many daily dates to keep scheduled ahead.")

    sub.add_parser("validate", help="Run quality gates on the bank that publish would write.")

    args = parser.parse_args(argv)
    if args.command == "wikidata":
        from pipeline.generate_wikidata import generate_wikidata
        return generate_wikidata(limit=args.limit, refresh=args.refresh, pageviews=args.pageviews, delay=args.delay, only=args.only)
    if args.command == "llm":
        from pipeline.generate_llm import generate_llm
        return generate_llm(count=args.count, url=args.url, model=args.model, timeout=args.timeout, refresh=args.refresh)
    if args.command == "report":
        from pipeline.report import run_report
        return run_report(sample=args.sample, prompt_id=args.id)
    if args.command == "publish":
        from pipeline.publish import publish
        return publish(days=args.days)
    if args.command == "validate":
        from pipeline.publish import validate
        return validate()
    parser.error(f"unknown command {args.command}")
    return 2
