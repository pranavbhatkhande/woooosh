# WOOOOSH prompt pipeline

Offline builder for the static bank in `data/`. The site does not need a model to boot. The optional live judge is a separate, disabled-by-default path documented at the bottom.

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
```

`think` is sent as `false`. If a build of Ollama rejects that field, the client retries once without it.

## Commands

```bash
python -m pipeline wikidata --target 280
python -m pipeline llm --count 8
python -m pipeline report
python -m pipeline publish
python -m pipeline check
```

- `wikidata` builds prompts from English Wikipedia categories (top incoming links) plus Wikidata sitelinks and aliases. Popularity is `log1p(sitelinks) * 2 + 0.15 * wordfreq zipf`. Pageviews are not fetched by default; one HTTP call per answer is too slow for a bulk run. Finished ids are cached in `pipeline/cache/` (gitignored) and skipped. Ids already in `data/index.json` are also skipped, so a weekly run adds new prompts instead of redoing the bank. Pass `--only wd-film-2019` to rebuild one job even if it is already published. `--retry-failed` clears the fail list for another attempt.
- `llm` asks the local model for new prompts, answer lists, a keep/drop check, then looks up the obscure names on English Wikipedia. Prompts under 40 solid answers, or missing a tier, are discarded. Results land in the same cache as Wikidata.
- `report` prints a spread of prompts (the published bank, or the cache if you have not published yet) plus any gem that looks like junk.
- `publish` writes `data/prompts/NNNN.json` and `data/index.json`. Curated prompts always overwrite the same id. Cached generations overwrite on a machine that has the cache, which is how a fix gets into the bank. A clone with no cache keeps the published prompts frozen. The version number changes only when the content hash changes. New ids append to the last shard (about 45 prompts) and then open a new file, so existing shard membership stays put.
- `check` lints the published bank and exits non-zero on a problem.
- `import-judged` folds answers the live judge accepted. See below. It does not retier the prompt. A judged answer is never the gem.

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

## Optional live judge

The game ships with the judge **off**. No Netlify env vars are set. The site scores from the bank only until you turn the judge on.

When a typed answer is not in the bank, the browser asks `POST /api/judge`. The Netlify Function looks up the prompt text itself (the client prompt text is ignored), then calls your model. Familiarity 10 is something almost everyone knows. The mapping is TAXI 9–10, CLIMB 7–8, BURN 5–6, STALL 3–4, APOGEE 1–2. The function never awards ESCAPE. If the model's canonical name is actually in the bank, the bank tier is returned instead, gem included, and it is not marked as judged.

If `JUDGE_URL` is unset, `GET /api/judge` returns `{"enabled": false}` and the page does not call it. If a call times out (about 4 seconds in the browser, 3.5 seconds in the function) or errors, the input just shakes, same as a bank miss. The 25 second clock is not paused.

### Do not publish Ollama directly

Ollama has no auth. Bind a small proxy to `127.0.0.1` and tunnel **that** port.

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

   The public URL looks like `https://<machine>.<tailnet>.ts.net`. The judge path is that origin plus `/v1`.

   Or Cloudflare Tunnel:

   ```bash
   cloudflared tunnel --url http://127.0.0.1:11435
   ```

   Use the `https://….trycloudflare.com` URL it prints, or a named tunnel you already run. Again, the origin must be the proxy.

4. Set the three Netlify variables on the site (Site configuration → Environment variables), then redeploy `main` so the function sees them:

   | Name | Value |
   | --- | --- |
   | `JUDGE_URL` | `https://<public-host>/v1` |
   | `JUDGE_MODEL` | `qwen3.8:27b` (this is the default if you omit it) |
   | `JUDGE_TOKEN` | the same secret as `JUDGE_PROXY_TOKEN` |

   `JUDGE_URL` ending in `/v1` uses the OpenAI-compatible chat endpoint. Ending in `/api` uses Ollama's native `/api/chat`. The proxy forwards both. Optional `JUDGE_API=ollama` or `openai` forces the shape if the URL has no suffix.

5. Confirm, then play.

   ```bash
   curl -sS https://woooosh.ai/api/judge
   # {"enabled":true}
   ```

   In the game, Settings → "AI judge for unlisted answers" defaults on only when that endpoint reports enabled. Players can turn it off. The toggle is forced off while the server reports disabled.

### Pulling accepted answers back into the bank

The function writes accepted judged answers to a Netlify Blobs store named `judge-accepted`, keyed by prompt id and normalized answer. Verdicts are also cached in `judge-verdicts`.

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

- Public Wikidata year-scans (`ORDER BY` over every film in a year) time out. Discovery is the top English Wikipedia category members by incoming links, then sitelinks and aliases from Wikidata. A year category can still include a reissue, a broadcast listing, or a very local title. `publish` drops broadcast-style titles (`on NBC`, and the same for the other big networks). If that removes the gem or knocks a prompt under 40 answers, the whole prompt is left out.
- The gem is the recognizable-rare slot inside that top slice, not a hand-picked favorite. Read `report` before you push a big update.
- Fuzzy matching is one edit on tokens of length 6 or more, and only when a single answer matches. Irregular plurals (`child` / `children`) are not special-cased.
- The in-function rate limit is per warm instance plus a best-effort per-IP cap. It is not a global account system.
- Adding prompt ids can change which seven the daily hash picks. Ids themselves stay stable.
- Tiers do not move after publish unless that prompt is rebuilt on purpose.
