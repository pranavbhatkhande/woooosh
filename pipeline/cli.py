"""python -m pipeline <command>"""

from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pipeline", description="Build the WOOOOSH prompt bank.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    wiki = sub.add_parser("wikidata", help="Generate prompts from Wikidata and Wikipedia categories")
    wiki.add_argument("--target", type=int, default=210)
    wiki.add_argument("--only", action="append", default=[], help="Run just this job id (repeatable)")
    wiki.add_argument("--retry-failed", action="store_true")
    wiki.add_argument("--refresh", action="store_true", help="Rebuild every job, including ones already published")

    llm = sub.add_parser("llm", help="Generate prompts with a local OpenAI-compatible or Ollama model")
    llm.add_argument("--count", type=int, default=10)
    llm.add_argument("--ping", action="store_true")
    llm.add_argument("--verbose", action="store_true", help="Print cache hits, batches, and each rejected idea")

    curated = sub.add_parser("curated", help="Expand hand prompts from Wikipedia categories")
    curated.add_argument("--only", action="append", default=[], help="Expand just this curated id (repeatable)")

    sub.add_parser("report", help="Print sample prompts from the published bank").add_argument("--count", type=int, default=8)
    sub.add_parser("fill", help="Expand open American prompts to their full answer sets")
    sub.add_parser("publish", help="Write versioned bank shards and data/index.json. Leaves data/prompts in place.")
    judged = sub.add_parser("import-judged", help="Fold accepted AI-judge answers into the bank")
    judged.add_argument("--file", default="")
    sub.add_parser("check", help="Lint the published bank and exit non-zero on problems")

    args = parser.parse_args(argv)
    if args.cmd == "wikidata":
        from pipeline.wikidata_run import generate

        generate(target=args.target, only=args.only or None, retry_failed=args.retry_failed, refresh=args.refresh)
        return 0
    if args.cmd == "llm":
        from pipeline.llm import run_llm

        return run_llm(count=args.count, ping=args.ping, verbose=args.verbose)
    if args.cmd == "curated":
        from pipeline.curated_harvest import harvest

        harvest(only=args.only or None)
        return 0
    if args.cmd == "report":
        from pipeline.report import run_report

        run_report(count=args.count)
        return 0
    if args.cmd == "fill":
        from pipeline.fill_sets import fill

        fill()
        return 0
    if args.cmd == "publish":
        from pipeline.publish import publish

        publish()
        return 0
    if args.cmd == "import-judged":
        from pipeline.import_judged import import_judged

        return import_judged(path=args.file or None)
    if args.cmd == "check":
        from pipeline.publish import check_bank

        return check_bank()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
