# Starting Strength

A tracker for Mark Rippetoe's barbell programs — Novice LP (Phases 1–3), Advanced
Novice, Texas Method, Heavy-Light-Medium, and a Four-Day Split. Every workout is
computed from your current work weights: alternations (press/bench, deadlift/clean),
percentage days, warm-up sets, plate loading per side, linear progression, stall
counting, and the 10% deload.

Zero dependencies, no build step. Vanilla ES modules + hand-rolled SVG charts.
Installable PWA (offline via service worker), works on iOS/Android/desktop,
light + dark themes, foldable-aware layout (`horizontal-viewport-segments`).

## Run

```sh
python3 -m http.server 8613
# open http://localhost:8613/
```

Any static file host works for deployment (GitHub Pages, Netlify, etc.) — the
service worker needs HTTPS or localhost. On a phone, open the URL and "Add to
Home Screen" to install.

## Demo mode

`#demo/<view>[/dark][/active]` renders a seeded 10-week history without touching
stored data — e.g. `/#demo/progress/dark` or `/#demo/today/active`.

## Layout

- `js/programs.js` — program/day/slot definitions and unit defaults
- `js/engine.js` — workout resolution, progression, warm-ups, plate math
- `js/store.js` — localStorage persistence, export/import
- `js/charts.js` — SVG line/bar charts with crosshair tooltips
- `js/app.js` — views and interaction
- `scratchpad test`: engine simulation suite (27 checks) exercised all seven
  programs through multi-cycle runs

All training data lives in localStorage; Settings → Export writes a JSON backup.
