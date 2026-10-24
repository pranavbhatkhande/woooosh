# WOOOOSH prompt pipeline

Offline builder for the static bank in `data/`. The live judge is a separate path: it turns on when `JUDGE_URL` is set, and the bank is the fallback. Details are at the bottom.

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

The judge is the primary scorer whenever `JUDGE_URL` is set. `GET /api/judge` returns `{"enabled": true}`. The live site points `JUDGE_URL` at an Ollama `/api` base (`https://cachybox.taila0628.ts.net/api`), which is a Tailscale Funnel in front of the token proxy, not raw Ollama. `JUDGE_MODEL` is `qwen3.8:27b`.

An exact or normalized bank hit, including aliases, returns from the function with no model call. Every other answer is sent to the model with a short list of near bank entries and a few common ones. That list is the lookup: the model has no web access. A typo, misspelling, plural, missing article, accent difference, abbreviation, or partial name maps back to the canonical bank row, so the player gets that tier and the answer is the bank entry. A real member that is not in the bank is accepted. A wrong answer is rejected and is not then fuzzy-matched.

Familiarity 10 is something almost everyone knows. Validity is separate: an obscure real member is still valid and scores a low familiarity (Joseph is a city in Oregon). The mapping is TAXI 9–10, CLIMB 7–8, BURN 5–6, STALL 3–4, APOGEE 1–2. The function never awards ESCAPE. If the model's canonical name is actually in the bank, the bank tier is returned instead, gem included, and it is not marked as judged.

If `JUDGE_URL` is unset, `GET /api/judge` returns `{"enabled": false}` and the page scores from the bank only. If a call errors, times out, or is rate limited, the game falls back to bank matching, including plurals and a unique one-edit typo. The 25 second clock is not paused.

Ollama requests send `keep_alive` of 30 minutes so a loaded model stays up. Starting a round also sends a warm request during the two-second preview. The function waits 8 seconds and the browser waits 9, inside Netlify's 10 second limit, so a cold load of about 5 seconds is not dropped.

### Do not publish Ollama directly

Ollama has no auth. Bind a small proxy to `127.0.0.1` and tunnel that port.

1. Create the secret and the env file. Use the same secret as Netlify's `JUDGE_TOKEN`.

   ```bash
   mkdir -p ~/.config/woooosh
   umask 077
   printf 'JUDGE_PROXY_TOKEN=%s\nJUDGE_PROXY_PORT=11435\nOLLAMA_UPSTREAM=http://127.0.0.1:11434\n' "$(openssl rand -hex 32)" > ~/.config/woooosh/judge.env
   chmod 600 ~/.config/woooosh/judge.env
   ```

2. Install the user service. The unit reads that env file and runs `deploy/judge_proxy.py` from the repo venv (stdlib only, besides the venv's Python).

   ```bash
   cp deploy/woooosh-judge-proxy.service ~/.config/systemd/user/
   # Edit ExecStart if the clone is not ~/woooosh.
   systemctl --user daemon-reload
   systemctl --user enable --now woooosh-judge-proxy.service
   systemctl --user status woooosh-judge-proxy.service
   curl -sS http://127.0.0.1:11435/healthz
   # {"ok":true}
   curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:11435/v1/chat/completions
   # 401
   ```

   Caddy is an equivalent proxy. See `deploy/Caddyfile.example`. Point it at port 11435 on localhost and keep Ollama on 11434.

3. Expose the proxy, not port 11434.

   Tailscale Funnel, from the machine that runs the proxy (Tailscale installed, Funnel allowed on the tailnet):

   ```bash
   tailscale funnel --bg 11435
   tailscale funnel status
   ```

   The public URL looks like `https://<machine>.<tailnet>.ts.net`. The current funnel is `https://cachybox.taila0628.ts.net`. Set `JUDGE_URL` to that origin plus `/api` for Ollama's native chat API, or plus `/v1` for the OpenAI-compatible API. The proxy forwards both.

   Or Cloudflare Tunnel:

   ```bash
   cloudflared tunnel --url http://127.0.0.1:11435
   ```

   Use the `https://….trycloudflare.com` URL it prints, or a named tunnel you already run. Again, the origin must be the proxy.

4. Set the three Netlify variables on the site (Site configuration → Environment variables). A deploy of `main` picks them up. They are already set for the live site.

   | Name | Value |
   | --- | --- |
   | `JUDGE_URL` | `https://<public-host>/api` |
   | `JUDGE_MODEL` | `qwen3.8:27b` (this is the default if you omit it) |
   | `JUDGE_TOKEN` | the same secret as `JUDGE_PROXY_TOKEN` |

   `JUDGE_URL` ending in `/api` uses Ollama's native `/api/chat`. Ending in `/v1` uses the OpenAI-compatible chat endpoint. Optional `JUDGE_API=ollama` or `openai` forces the shape if the URL has no suffix.

5. Confirm, then play.

   ```bash
   curl -sS https://woooosh.ai/api/judge
   # {"enabled":true}
   ```

   In the game, Settings → "AI judge for close and unlisted answers" defaults on only when that endpoint reports enabled. Players can turn it off. The toggle is forced off while the server reports disabled.

### Pulling accepted answers back into the bank

The function writes accepted judged answers to a Netlify Blobs store named `judge-accepted`, keyed by prompt id and normalized answer. Verdicts are also cached in `judge-verdicts`. A verdict that mapped onto a bank entry is cached, and it is not written to `judge-accepted`, because it is not a new answer.

```bash
export NETLIFY_SITE_ID=your-site-id
export NETLIFY_AUTH_TOKEN=a-token-that-can-read-blobs
node deploy/pull-judged.mjs
python -m pipeline import-judged
python -m pipeline check
git add data
git commit -m "Fold judged answers into the bank"
git push origin main
```

`import-judged` appends at the judged tier, skips names that already match, refuses the gem tier, and does not reshuffle existing answers. An answer logged as ESCAPE is stored as APOGEE.

## What the generator will not do

- Year-pinned prompts ("released in 1999", "premiered in 2004", and ids such as `wd-film-2015`) are not generated. `publish` drops any that are still in the bank. "Name a Best Picture winner" and "Name an Album of the Year winner" stay: the award is not a calendar year. The model idea filter rejects a four-digit year for the same reason. `publish` still drops broadcast-style titles (`on NBC`, and the same for the other big networks).
- The gem is the recognizable-rare slot inside that top slice, not a hand-picked favorite. Read `report` before you push a big update.
- Bank fuzzy matching is one edit on tokens of length 6 or more, and only when a single answer matches. Irregular plurals (`child` / `children`) are not special-cased. The live judge runs before that fallback and is more lenient.
- The in-function rate limit is per warm instance plus a best-effort per-IP cap. It is not a global account system.
- The daily ascent does not call a model and does not need cachybox. The browser sorts prompt ids by a stable hash (`woooosh-deck|<id>`), splits that deck into blocks of seven, and uses the UTC day number since 2026-01-01 to pick the block. Consecutive days do not share a prompt. A prompt returns after `floor(count / 7)` days. The home screen rolls the label at 00:00 UTC (evening in the Americas, morning in Asia). Adding ids can change which block a later day lands on, because the deck is the whole bank; today's block is still a pure function of the UTC date and the published ids. `deploy/weekly.sh` is optional and only adds future prompts (Wikidata jobs still in the catalog, plus a few model ideas). If that timer is not installed, or cachybox is down, the daily still changes every UTC day from the bank already shipped.
- Tiers do not move after publish unless that prompt is rebuilt on purpose.
