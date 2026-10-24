#!/bin/sh
# Add a handful of new prompts, publish shards, and push main.
# Keeps the pipeline cache on this machine so finished jobs are not redone.
set -eu

cd "$(dirname "$0")/.."
mkdir -p pipeline/cache/accepted
LOCK="${WOOOOSH_LOCK:-$HOME/.cache/woooosh-weekly.lock}"
mkdir -p "$(dirname "$LOCK")"

if command -v flock >/dev/null 2>&1; then
  exec 9>"$LOCK"
  flock -n 9 || { echo "weekly already running"; exit 0; }
fi

if [ -f .venv/bin/activate ]; then
  # shellcheck disable=SC1091
  . .venv/bin/activate
fi

NEW="${WEEKLY_NEW:-12}"
HAVE="$(find pipeline/cache/accepted -name 'wd-*.json' 2>/dev/null | wc -l | tr -d ' ')"
PUBLISHED="$(python - <<'PY'
import json
from pathlib import Path
index = Path("data/index.json")
if not index.exists():
    print(0)
else:
    data = json.loads(index.read_text())
    print(sum(1 for shard in data.get("shards") or [] for prompt_id in shard.get("ids") or [] if str(prompt_id).startswith("wd-")))
PY
)"
TARGET=$((PUBLISHED + NEW))
if [ "$HAVE" -gt "$TARGET" ]; then
  TARGET=$HAVE
fi

echo "wikidata target $TARGET (published $PUBLISHED, cached $HAVE, plus $NEW)"
python -m pipeline llm --count "${WEEKLY_LLM:-4}" || echo "llm step failed; continuing with what is cached"
python -m pipeline wikidata --target "$TARGET"
python -m pipeline publish
python -m pipeline check

git add data
if git diff --cached --quiet; then
  echo "no bank changes"
  exit 0
fi
git commit -m "Add prompts from the weekly pipeline"
git push origin main
