# WOOOOSH

Seven prompts. Rarer answers climb higher.

A run is seven open prompts. Each one shows for two seconds, then a 25-second clock. You type one answer. The first answer in the bank locks in. Anything else shakes the box and you keep trying. Pass or time out and that prompt is zero. The run always finishes all seven.

Rarer answers score more height. One point is one kilometer.

| Tier | Points | Meaning |
| --- | --- | --- |
| TAXI | 5 | The obvious answer |
| CLIMB | 10 | Off the pad |
| BURN | 25 | A solid, less common pick |
| STALL | 40 | The too-clever trap: the deep cut that is not actually rare |
| APOGEE | 60 | High, and actually rare |
| ESCAPE | 100 | The single gem on that prompt |

Daily is the same seven prompts for every player, chosen from the UTC date. Open sky shuffles prompts you have not seen, then starts over from the oldest. Streak, best altitude, and the seen list stay in this browser.

Answers score only when they are in the bank. There is no live model on the site. See [pipeline/README.md](pipeline/README.md) for the owner's commands and the weekly timer.

The bank is static JSON in `data/`, built offline.

```bash
npm test
python -m unittest discover -s pipeline/tests -v
```
