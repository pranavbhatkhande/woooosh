# WOOOOSH

Seven prompts. Rarer answers climb higher.

A run is seven open prompts. Each one shows for two seconds, then a 25 second clock. Type one answer. The first match locks in. A miss shakes the box and costs nothing. Pass or a timeout scores 0, and the run still plays all seven.

One point is one kilometre. Tiers, from common to rare: Pad 5, Ascent 10, Ceiling 25, Hotshot 40, Orbit 60, Apex 100. Hotshot is the trap: the clever pick everyone reaches for that is not actually rare. Each prompt has one Apex gem.

Daily is the same seven prompts for every player on a UTC day. Unlimited does not repeat a prompt until this browser has seen the whole bank, then it replays oldest first. Streak and best altitude stay in local storage on this browser.

The prompt bank is static JSON. There is no live model on the site. New prompts are built offline with the tools in [pipeline/README.md](pipeline/README.md).

Netlify publishes this repo from `main` with no build step (`netlify.toml`, `publish = "."`).

## Play it locally

```bash
python3 -m http.server 8765
```

Open `http://127.0.0.1:8765/`. The game loads `/data/index.json`, so it has to be served from the repo root.

## Tests

```bash
node --test tests/matcher.test.mjs tests/engine.test.mjs
python -m unittest discover -s pipeline/tests
```

The display face is [Silkscreen](fonts/OFL.txt), used under the SIL Open Font License. Prompt text uses the system font.
