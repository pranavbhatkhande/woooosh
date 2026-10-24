# WOOOOSH prompt pipeline

Offline generator for the static prompt bank. The site never calls a model. This package writes JSON under `data/`, and Netlify serves those files from `main`.

Python 3.11+ (the owner box runs 3.14). Tested with 3.12. Dependencies are `requests` and `wordfreq`.

## Setup

```bash
git clone https://github.com/pranavbhatkhande/woooosh.git ~/woooosh
cd ~/woooosh
python3 -m venv .venv
source .venv/bin/activate
pip install -r pipeline/requirements.txt
```

Ollama should already be serving `qwen3.8:27b` at `http://localhost:11434` (OpenAI-compatible `/v1/chat/completions`). Override the model and URL if needed:

```bash
export WOOOOSH_LLM_URL=http://localhost:11434/v1
export WOOOOSH_LLM_MODEL=qwen3.8:27b
```

The same two variables are read by the CLI defaults. Flags `--url` and `--model` win over the environment.

Git needs a name and email on this machine (`git config user.name`, `git config user.email`). The scripts do not change git config. Push access to `main` has to already work (`git push origin main`).

## Commands

From `~/woooosh` with the venv active:

```bash
python -m pipeline wikidata
python -m pipeline llm --count 25
python -m pipeline report
python -m pipeline report --id wd-countries
python -m pipeline publish
python -m pipeline validate
```

- `wikidata` runs every template in `pipeline/templates.py`. Output lands in `pipeline/out/prompts/wd-<id>.json` (gitignored). Re-running skips files that already exist. `--refresh` rebuilds them. `--only countries,elements` limits the run. `--limit 20` stops after that many newly accepted prompts. `--pageviews` adds a slow English Wikipedia pageview pass. `--delay 1.05` is the pause between network calls.
- `llm` asks the local model for new prompt ideas, expands answer lists, checks them, and writes `pipeline/out/prompts/llm-*.json`. `--count` is how many new prompts to accept, not how many to attempt. Rejected ideas are remembered under `pipeline/out/llm-rejected/` so the next run skips them. Cache for model replies is `pipeline/.cache/llm/`.
- `report` prints a sample of whatever `publish` would ship, including tier counts and one example per tier.
- `publish` merges three sources, in order: the current `data/` shards, `pipeline/out/prompts/*.json`, then `pipeline/curated/prompts.txt`. Later sources win on the same id. It drops anything that fails the gates, writes `data/prompts/NNNN.json`, `data/index.json`, and `data/daily.json`, and bumps `version` only when the bank or the schedule actually changes.
- `validate` runs the same gates and prints drops, without writing.

Hand-written prompts use the block format in `pipeline/curated/prompts.txt`. One `---` starts a prompt. Header lines are `key: value` with no pipe. Answer lines are `Name | tier | alias;alias | gem`. Tiers are `pad`, `ascent`, `ceiling`, `hotshot`, `orbit`, `apex`. Mark exactly one apex row with `gem`.

## What a good prompt has to pass

- At least 40 answers.
- All six tiers present, and no tier above 45% of the list.
- Exactly one gem, and it is apex.
- No two answers (or aliases) collapse to the same key after the matcher rules. Near-duplicate names are repaired before this check on generated prompts.
- No profanity as a whole token. Substrings are kept, so names like Assam stay.

Wikidata rarity is within the prompt: sitelink count, plus a light English word-frequency nudge. Pageviews are off unless you pass `--pageviews`. The gem is the most recognizable name in the rarest band, not the most obscure tail. Hotshot is the upper-middle band: the clever pick that is not actually rare.

LLM rarity uses the model's familiarity score (1 = everyone says it, 6 = rare) plus wordfreq. Prompts with fewer than 40 answers that survive verification are rejected. Factual prompts are also checked against Wikipedia titles when the idea is marked factual.

Runs are safe to stop. SPARQL, Wikipedia, and model replies are cached under `pipeline/.cache/` (gitignored). Start the same command again and finished prompts are skipped.

## Tests

```bash
python -m unittest discover -s pipeline/tests
node --test tests/matcher.test.mjs tests/engine.test.mjs
```

## Weekly timer

The example units live in `pipeline/deploy/`. They assume the clone is `~/woooosh` and the venv is `~/woooosh/.venv`. The timer runs Sunday 03:30 local time, catches up if the machine was off, and waits up to 30 minutes so it does not stampede.

`weekly-generate.sh` pulls `main`, fills any missing Wikidata templates, asks the model for `WOOOOSH_WEEKLY_COUNT` new prompts (default 25), publishes, and pushes a normal commit to `main` when `data/` changed. It refuses to run if the tree is dirty, the branch is not `main`, or git identity is unset. It does not force-push.

```bash
chmod +x ~/woooosh/pipeline/deploy/weekly-generate.sh
mkdir -p ~/.config/systemd/user
cp ~/woooosh/pipeline/deploy/woooosh-pipeline.service ~/.config/systemd/user/
cp ~/woooosh/pipeline/deploy/woooosh-pipeline.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now woooosh-pipeline.timer
loginctl enable-linger "$USER"
systemctl --user list-timers woooosh-pipeline.timer
```

Run it once by hand with `systemctl --user start woooosh-pipeline.service` and read `journalctl --user -u woooosh-pipeline.service`.

Change the model, URL, or weekly count in the service file's `Environment=` lines, then `systemctl --user daemon-reload`.

## Data files

`data/index.json` lists the version, content hash, prompt count, tier table, and shards. Each shard is `data/prompts/0001.json` with a `prompts` array. `data/daily.json` pins the seven ids for each UTC date so growing the bank does not reshuffle a day that was already scheduled.

A prompt looks like this:

```json
{
  "id": "wd-countries",
  "text": "Name a country",
  "category": "geography",
  "source": "wikidata",
  "answers": [
    {"name": "France", "aliases": ["French Republic"], "tier": "pad", "gem": false, "qid": "Q142"}
  ]
}
```

`qid` is present on Wikidata answers and omitted on hand and model answers. `source` is `wikidata`, `hand`, or `llm`.
