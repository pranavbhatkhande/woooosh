# woooosh

A static guide for the October 20, 2026 recomp plan: the coach’s summary, three weekly training templates, a protein and calorie calculator that uses the plan’s ranges, sleep, supplements, a weekly check-in stored in this browser, and the reference list.

Not medical advice.

## Run

```sh
python3 -m http.server 8613
```

Open http://localhost:8613/

## Deploy

Netlify serves this repository with `publish = "."` in `netlify.toml`. There is no build step. The custom domain is attached to that Netlify site; this repo does not contain a CNAME or a GitHub Actions workflow.
