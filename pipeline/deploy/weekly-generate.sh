#!/usr/bin/env bash
# Add prompts on the owner's machine, publish shards, and push main.
# Netlify deploys main. This script does not rewrite git history or git config.
set -euo pipefail

cd "$(dirname "$0")/../.."

if [[ ! -d .venv ]]; then
  echo "Missing .venv in $(pwd). Create it with: python3 -m venv .venv && .venv/bin/pip install -r pipeline/requirements.txt" >&2
  exit 1
fi

# shellcheck disable=SC1091
source .venv/bin/activate

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Working tree is dirty. Refusing to commit over local edits." >&2
  exit 1
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$branch" != "main" ]]; then
  echo "Weekly job expects branch main (current: ${branch})." >&2
  exit 1
fi

if ! git config user.email >/dev/null || ! git config user.name >/dev/null; then
  echo "Set git user.name and user.email on this machine. This script will not write git config." >&2
  exit 1
fi

git pull --ff-only origin main

# Fill any Wikidata templates that do not have an output file yet.
# A failed template is logged and skipped; already-built files are left alone.
python -m pipeline wikidata || echo "Wikidata reported template failures. Continuing."

python -m pipeline llm --count "${WOOOOSH_WEEKLY_COUNT:-25}"
python -m pipeline publish

git add data
if git diff --cached --quiet; then
  echo "No bank changes to commit."
  exit 0
fi

git commit -m "Add weekly prompts to the WOOOOSH bank"
git push origin main
