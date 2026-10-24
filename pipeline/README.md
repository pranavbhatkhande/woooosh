# WOOOOSH prompt pipeline

Offline builder for the static bank in `data/`. The site never calls a model. `GET /api/judge` stays `{"enabled": false}` even if `JUDGE_URL` is set in Netlify.

Python 3.11 or newer (3.14 on the owner's box is fine). The only package is `wordfreq`.

```bash
git clone https://github.com/pranavbhatkhande/woooosh.git
cd woooosh
python3 -m venv .venv
source .venv/bin/activate
pip install -r pipeline/requirements.txt
```

Ollama on this machine should already be serving the model:

```bash
# native API:        http://127.0.0.1:11434/api/chat
# OpenAI-compatible: http://127.0.0.1:11434/v1/chat/completions
export PIPELINE_LLM_URL=http://127.0.0.1:11434
export PIPELINE_LLM_MODEL=qwen3.8:27b
python -m pipeline llm --ping
python -m pipeline llm --count 8 --verbose
```

`--verbose` prints why an idea was rejected. A run that adds nothing still leaves the raw replies in `pipeline/cache/llm/raw/` for inspection. Publish after a run that adds prompts you want on the site.

`think` is sent as `false`. If a build of Ollama rejects that field, the client retries once without it.

## Commands

```bash
python -m pipeline wikidata --target 280
python -m pipeline curated
python -m pipeline llm --count 8 --verbose
python -m pipeline report
python -m pipeline publish
python -m pipeline check
```

- `wikidata` builds prompts from every main-namespace page in the English Wikipedia category (paginated category members, not a top-70 sample). Thin categories also walk subcategories. Sitelink counts and English aliases come from Wikidata. Popularity is `log1p(sitelinks) * 2 + 0.15 * wordfreq zipf`, then percentile tiers, so most of a long list lands in STALL and APOGEE. Pageviews are not fetched. Finished ids are cached in `pipeline/cache/` (gitignored) and skipped. Ids already in `data/index.json` are also skipped, so a weekly run adds new prompts instead of redoing the bank. Pass `--only wd-film-2019` to rebuild one job even if it is already published. `--refresh` rebuilds every job, including published ones. `--retry-failed` clears the fail list for another attempt.
- `curated` expands the hand lists from the same exhaustive category harvest, for prompts whose category is a real set (spices, pasta, films of a kind, and so on). A failed harvest leaves the hand list alone.
- `llm` asks the local model for new prompts with large answer spaces, three batches of answers, and a keep/drop check, then looks up the obscure names on English Wikipedia. Ideas that repeat the bank, or name a tiny closed set, are dropped. Tiers are percentile ranks, so a flat familiarity spread still fills every tier. Raw replies are cached under `pipeline/cache/llm/raw/` and reused; a reply that did not parse is not treated as a hit. `--verbose` prints cache hits, batch sizes, and each rejected idea. Skip lines always include a familiarity histogram. Prompts under 40 solid answers are discarded. Accepted prompts land in `pipeline/cache/accepted/` and are not in the live bank until `publish`.
- `report` prints a spread of prompts (the published bank, or the cache if you have not published yet) plus any gem that looks like junk.
- `publish` writes `data/prompts/NNNN.json` and `data/index.json`. Shard files are packed to about 1.2 MB, and a single oversized prompt gets its own file. A cached copy replaces a published prompt only when it is not a much shorter list, so an old 70-answer cache cannot shrink an exhaustive bank. Hand lists fill gaps and replace a prompt only when they are longer. Once a film, game, album, television, or city kind has an exhaustive bank, leftover prompts of that kind that are still at the old ~70 cap are dropped. A clone with no cache keeps the published prompts frozen. The version number changes only when the content hash changes.
- `check` lints the published bank and exits non-zero on a problem.

Generate, look at `report`, then:

```bash
python -m pipeline publish
python -m pipeline check
git add data
git commit -m "Update the prompt bank"
git push origin main
```

Netlify deploys `main` on its own. Do not force-push.

## Weekly timer

`deploy/weekly.sh` adds Wikidata prompts (default 12, `WEEKLY_NEW`) and a few model prompts (`WEEKLY_LLM`, default 4), publishes, and pushes `main` when `data/` changed. It keeps `pipeline/cache/` so old jobs are not repeated.

```bash
chmod +x deploy/weekly.sh
mkdir -p ~/.config/systemd/user
cp deploy/woooosh-weekly.service deploy/woooosh-weekly.timer ~/.config/systemd/user/
# If the clone is not ~/woooosh, edit the paths in the service.
systemctl --user daemon-reload
systemctl --user enable --now woooosh-weekly.timer
loginctl enable-linger "$USER"
systemctl --user list-timers woooosh-weekly.timer
```

Run it once by hand to confirm git can push:

```bash
./deploy/weekly.sh
```

## Tests

```bash
python -m unittest discover -s pipeline/tests -v
node --test tests/*.test.mjs
```

## Live judge

There is no live model endpoint. `netlify/functions/judge.js` returns `{"enabled": false}` for every request and does not read `JUDGE_URL`. A typed answer that is not in the bank only shakes the input. The helpers in `netlify/lib/judge-core.js` are covered by unit tests and are not used by the handler while that guard is in place.

Confirm after a deploy:

```bash
curl -sS https://woooosh.ai/api/judge
# {"enabled":false}
```

## What the generator will not do

- Public Wikidata year-scans (`ORDER BY` over every film in a year) time out. Discovery is the top English Wikipedia category members by incoming links, then sitelinks and aliases from Wikidata. A year category can still include a reissue, a broadcast listing, or a very local title. `publish` drops broadcast-style titles (`on NBC`, and the same for the other big networks). If that removes the gem or knocks a prompt under 40 answers, the whole prompt is left out.
- The gem is the recognizable-rare slot inside that top slice, not a hand-picked favorite. Read `report` before you push a big update.
- Fuzzy matching is one edit on tokens of length 6 or more, and only when a single answer matches. Irregular plurals (`child` / `children`) are not special-cased.
- Adding prompt ids can change which seven the daily hash picks. Ids themselves stay stable.
- Tiers do not move after publish unless that prompt is rebuilt on purpose.
