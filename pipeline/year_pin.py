"""Date-pinned trivia is a bad daily. A calendar year in the prompt is enough.

Kept on purpose: "Name a Best Picture winner" and "Name an Album of the Year
winner". Those name the award, not one release year, so the text has no
calendar year. Ids such as wd-film-2015 are pinned even if the wording changes.
"""

from __future__ import annotations

import re

_YEAR = re.compile(r"\b(?:1[89]\d{2}|20\d{2})\b")
_ID = re.compile(r"^wd-(?:film|album|game|tv|tvuk|song|book)-\d{4}$")


def year_pinned(prompt: dict) -> bool:
    if _ID.match(str(prompt.get("id") or "")):
        return True
    return bool(_YEAR.search(str(prompt.get("text") or "")))
