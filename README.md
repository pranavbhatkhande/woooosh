# WOOOOSH

Seven prompts. Rarer answers climb higher.

A run is seven open prompts. Each one shows for two seconds, then a 25-second clock. You type one answer. An exact bank match locks in at once. Other answers go to the judge, and if the judge is down the bank's close-match rules are used. A miss shakes the box and you keep trying. Pass or time out and that prompt is zero. The run always finishes all seven.

Rarer answers score more height. One point is one kilometer.

| Tier | Points | Meaning |
| --- | --- | --- |
| TAXI | 5 | The obvious answer |
| CLIMB | 10 | Off the pad |
| BURN | 25 | A solid, less common pick |
| STALL | 40 | The too-clever trap: the deep cut that is not actually rare |
| APOGEE | 60 | High, and actually rare |
| ESCAPE | 100 | The single gem on that prompt |

Daily is the same seven prompts for every player. The bank is ordered once by a stable hash of each prompt id. Each UTC day takes the next block of seven, so a prompt does not come back until every full block has been used, and the day changes at 00:00 UTC. A home screen left open past midnight shows the new date. The rotation runs in the browser from the published bank. Open sky shuffles prompts you have not seen, then starts over from the oldest. Streak, best altitude, and the seen list stay in this browser.

An exact bank match scores immediately. Anything else goes to the AI judge when `JUDGE_URL` is set: a close spelling maps back to that bank entry, and a real answer that is not listed can still score. The play clock pauses only while that request is in flight, including an answer sent with a second left, and it resumes when the verdict or the bank fallback comes back. The warm-up request does not pause the clock. Judged answers are marked and never receive the gem. If the judge errors, times out, or is rate limited, scoring falls back to the bank. See [pipeline/README.md](pipeline/README.md) for the owner's commands, the weekly timer, and how the model is exposed.

The bank is static JSON in `data/`, built offline.

```bash
npm test
python -m unittest discover -s pipeline/tests -v
```
