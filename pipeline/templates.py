"""Wikidata prompt templates. QIDs were checked against live labels before use."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Template:
    id: str
    text: str
    category: str
    sparql: str
    min_sitelinks: int = 8
    limit: int = 100


def _query(patterns: str, limit: int, min_sitelinks: int) -> str:
    return f"""SELECT DISTINCT ?item ?label ?sitelinks WHERE {{
  {patterns}
  ?item wikibase:sitelinks ?sitelinks .
  FILTER(?sitelinks >= {int(min_sitelinks)})
  ?item rdfs:label ?label .
  FILTER(LANG(?label) = "en")
}}
ORDER BY DESC(?sitelinks)
LIMIT {int(limit)}
"""


def _simple(identifier, text, category, patterns, min_sitelinks, limit):
    return Template(identifier, text, category, _query(patterns, limit, min_sitelinks), min_sitelinks, limit)


def _p(prop, qid):
    return f"?item wdt:{prop} wd:{qid} ."


def _union_p31_p279(qid):
    return f"""{{
  ?item wdt:P31 wd:{qid} .
}} UNION {{
  ?item wdt:P279 wd:{qid} .
}}"""


def all_templates() -> list[Template]:
    templates: list[Template] = []
    templates.extend(_core())
    templates.extend(_people())
    templates.extend(_places())
    templates.extend(_culture())
    templates.extend(_genres())
    templates.extend(_cities())
    templates.extend(_years())
    seen = set()
    unique = []
    for template in templates:
        if template.id in seen:
            raise ValueError(f"duplicate template {template.id}")
        seen.add(template.id)
        unique.append(template)
    return unique


def _core() -> list[Template]:
    rows = [
        ("elements", "Name a chemical element", "science", _p("P31", "Q11344"), 1, 130),
        ("countries", "Name a country", "geography", _p("P31", "Q3624078"), 5, 220),
        ("us-states", "Name a US state", "geography", _p("P31", "Q35657"), 1, 60),
        ("constellations", "Name a constellation", "science", _p("P31", "Q8928"), 1, 100),
        ("languages", "Name a language", "language", _p("P31", "Q34770"), 15, 120),
        ("writing-systems", "Name a writing system", "language", _p("P31", "Q8192"), 5, 100),
        ("currencies", "Name a currency", "geography", _p("P31", "Q8142"), 12, 120),
        ("programming-languages", "Name a programming language", "technology", _p("P31", "Q9143"), 6, 100),
        ("religions", "Name a religion", "culture", "?item wdt:P31/wdt:P279* wd:Q9174 .", 8, 80),
        ("dog-breeds", "Name a dog breed", "animals", _p("P31", "Q39367"), 3, 140),
        ("cat-breeds", "Name a cat breed", "animals", _p("P31", "Q43577"), 3, 120),
        ("horse-breeds", "Name a horse breed", "animals", _p("P31", "Q1160573"), 3, 120),
        ("rivers", "Name a river", "geography", _p("P31", "Q4022"), 20, 100),
        ("lakes", "Name a lake", "geography", _p("P31", "Q23397"), 18, 100),
        ("mountains", "Name a mountain", "geography", _p("P31", "Q8502"), 25, 100),
        ("volcanoes", "Name a volcano", "geography", _p("P31", "Q8072"), 15, 100),
        ("islands", "Name an island", "geography", _p("P31", "Q23442"), 30, 100),
        ("airports", "Name an airport", "travel", _p("P31", "Q1248784"), 25, 100),
        ("airlines", "Name an airline", "travel", _p("P31", "Q46970"), 10, 100),
        ("universities", "Name a university", "places", "?item wdt:P31/wdt:P279* wd:Q3918 .", 30, 80),
        ("museums", "Name a museum", "culture", """{
  ?item wdt:P31 wd:Q33506 .
} UNION {
  ?item wdt:P31 wd:Q207694 .
} UNION {
  ?item wdt:P31 wd:Q1007870 .
}""", 15, 100),
        ("us-parks", "Name a US national park", "geography", "?item wdt:P31 wd:Q46169 . ?item wdt:P17 wd:Q30 .", 2, 80),
        ("tube", "Name a London Underground station", "travel", _p("P31", "Q14562709"), 2, 140),
        ("heritage", "Name a UNESCO World Heritage Site", "places", _p("P1435", "Q9259"), 18, 100),
        ("landlocked", "Name a landlocked country", "geography", _p("P31", "Q123480"), 4, 80),
        ("moons", "Name a moon in the Solar System", "science", _p("P31", "Q2537"), 18, 80),
        ("newspapers", "Name a newspaper", "culture", _p("P31", "Q11032"), 15, 100),
        ("magazines", "Name a magazine", "culture", _p("P31", "Q41298"), 12, 100),
        ("board-games", "Name a board game", "play", _p("P31", "Q131436"), 8, 100),
        ("instruments", "Name a musical instrument", "music", _p("P31", "Q34379"), 8, 100),
        ("gemstones", "Name a gemstone", "science", _p("P31", "Q83437"), 5, 80),
        ("software", "Name a piece of software", "technology", _p("P31", "Q7397"), 28, 100),
        ("game-devs", "Name a video game developer", "play", _p("P31", "Q210167"), 8, 100),
        ("automakers", "Name a car manufacturer", "technology", _p("P31", "Q786820"), 6, 100),
        ("olympic-sports", "Name an Olympic sport", "sport", _p("P31", "Q212434"), 2, 80),
        ("tarot", "Name a tarot card", "play", _p("P31", "Q12058324"), 1, 90),
        ("beer-styles", "Name a beer style", "food", _p("P31", "Q1998962"), 3, 100),
        ("capitals", "Name a national capital", "geography", "?country wdt:P31 wd:Q3624078 . ?country wdt:P36 ?item .", 8, 200),
        ("teams", "Name an NBA, NFL, MLB, or NHL team", "sport", """{
  ?item wdt:P118 wd:Q155223 . ?item wdt:P31/wdt:P279* wd:Q12973014 .
} UNION {
  ?item wdt:P118 wd:Q1215884 . ?item wdt:P31/wdt:P279* wd:Q12973014 .
} UNION {
  ?item wdt:P118 wd:Q1163715 . ?item wdt:P31/wdt:P279* wd:Q12973014 .
} UNION {
  ?item wdt:P118 wd:Q1215892 . ?item wdt:P31/wdt:P279* wd:Q12973014 .
}""", 4, 160),
    ]
    union_rows = [
        ("cheeses", "Name a cheese", "food", "Q10943", 3, 100),
        ("pastas", "Name a pasta shape", "food", "Q178", 2, 80),
        ("breads", "Name a kind of bread", "food", "Q7802", 2, 80),
        ("fruits", "Name a fruit", "food", "Q3314483", 2, 80),
        ("spices", "Name a spice", "food", "Q42527", 2, 80),
        ("cocktails", "Name a cocktail", "food", "Q134768", 4, 100),
        ("martial-arts", "Name a martial art", "sport", "Q11417", 3, 80),
        ("dances", "Name a dance", "culture", "Q11639", 8, 80),
    ]
    templates = [_simple(*row) for row in rows]
    for identifier, text, category, qid, minimum, limit in union_rows:
        templates.append(_simple(identifier, text, category, _union_p31_p279(qid), minimum, limit))
    continents = [
        ("africa", "Africa", "Q15"),
        ("asia", "Asia", "Q48"),
        ("europe", "Europe", "Q46"),
        ("north-america", "North America", "Q49"),
        ("south-america", "South America", "Q18"),
        ("oceania", "Oceania", "Q55643"),
    ]
    for slug, label, qid in continents:
        patterns = f"?item wdt:P31 wd:Q3624078 . ?item wdt:P30 wd:{qid} ."
        templates.append(_simple(f"countries-{slug}", f"Name a country in {label}", "geography", patterns, 4, 80))
    return templates


def _people() -> list[Template]:
    occupations = [
        ("singers", "Name a singer", "Q177220", 25),
        ("footballers", "Name a footballer", "Q937857", 25),
        ("basketball-players", "Name a basketball player", "Q3665646", 15),
        ("painters", "Name a painter", "Q1028181", 20),
        ("poets", "Name a poet", "Q49757", 15),
        ("philosophers", "Name a philosopher", "Q4964182", 15),
        ("mathematicians", "Name a mathematician", "Q170790", 15),
        ("physicists", "Name a physicist", "Q169470", 15),
        ("inventors", "Name an inventor", "Q205375", 12),
        ("astronauts", "Name an astronaut", "Q11631", 4),
    ]
    positions = [
        ("us-presidents", "Name a US president", "Q11696", 1, 60),
        ("uk-premiers", "Name a British prime minister", "Q14211", 4, 80),
        ("popes", "Name a pope", "Q19546", 12, 80),
        ("emperors", "Name a Roman emperor", "Q842606", 8, 80),
        ("pharaohs", "Name a pharaoh", "Q37110", 8, 80),
    ]
    awards = [
        ("best-picture", "Name a Best Picture winner", "Q102427", 8, 120),
        ("nobel-physics", "Name a Nobel laureate in Physics", "Q38104", 8, 120),
        ("nobel-chemistry", "Name a Nobel laureate in Chemistry", "Q44585", 8, 120),
        ("nobel-medicine", "Name a Nobel laureate in Medicine", "Q80061", 8, 120),
        ("nobel-literature", "Name a Nobel laureate in Literature", "Q37922", 6, 120),
        ("nobel-peace", "Name a Nobel Peace Prize laureate", "Q35637", 8, 120),
        ("palme", "Name a Palme d'Or winner", "Q179808", 6, 100),
        ("booker", "Name a Booker Prize winner", "Q160082", 4, 80),
    ]
    templates = []
    for identifier, text, qid, minimum in occupations:
        templates.append(_simple(identifier, text, "people", _p("P106", qid), minimum, 100))
    # Humans only, so fictional office-holders do not become Apex answers.
    for identifier, text, qid, minimum, limit in positions:
        patterns = f"?item wdt:P39 wd:{qid} . ?item wdt:P31 wd:Q5 ."
        templates.append(_simple(identifier, text, "people", patterns, minimum, limit))
    film_awards = {"best-picture", "palme"}
    for identifier, text, qid, minimum, limit in awards:
        if identifier in film_awards:
            patterns = f"?item wdt:P166 wd:{qid} . ?item wdt:P31 wd:Q11424 ."
        elif identifier == "booker":
            patterns = f"""?item wdt:P166 wd:{qid} . {{
  ?item wdt:P31 wd:Q8261 .
}} UNION {{
  ?item wdt:P31 wd:Q7725634 .
}}"""
            text = "Name a Booker-winning book"
        else:
            patterns = f"?item wdt:P166 wd:{qid} . ?item wdt:P31 wd:Q5 ."
        templates.append(_simple(identifier, text, "culture", patterns, minimum, limit))
    templates.append(_simple(
        "oscar-actors",
        "Name an Oscar-winning actor",
        "people",
        """{
  ?item wdt:P166 wd:Q103916 .
} UNION {
  ?item wdt:P166 wd:Q103618 .
} UNION {
  ?item wdt:P166 wd:Q106301 .
} UNION {
  ?item wdt:P166 wd:Q106291 .
}
?item wdt:P31 wd:Q5 .""",
        4,
        140,
    ))
    templates.append(_simple(
        "classical-composers",
        "Name a classical composer",
        "people",
        """?item wdt:P106 wd:Q36834 . {
  ?item wdt:P136 wd:Q9730 .
} UNION {
  ?item wdt:P136 wd:Q8361 .
} UNION {
  ?item wdt:P136 wd:Q17723 .
} UNION {
  ?item wdt:P136 wd:Q207591 .
}""",
        10,
        100,
    ))
    templates.append(_simple(
        "paintings", "Name a painting", "culture", _p("P31", "Q3305213"), 18, 100,
    ))
    templates.append(_simple(
        "novels", "Name a novel", "culture", _p("P31", "Q8261"), 22, 100,
    ))
    templates.append(_simple(
        "animated-films", "Name an animated film", "film",
        "?item wdt:P31 wd:Q11424 . ?item wdt:P136 wd:Q202866 .", 12, 100,
    ))
    return templates


def _places() -> list[Template]:
    return []


def _culture() -> list[Template]:
    return []


def _genres() -> list[Template]:
    genres = [
        ("rock", "rock", "Q11399"),
        ("pop", "pop", "Q37073"),
        ("jazz", "jazz", "Q8341"),
        ("hip-hop", "hip hop", "Q11401"),
        ("metal", "heavy metal", "Q38848"),
        ("electronic", "electronic", "Q9778"),
        ("country", "country", "Q83440"),
        ("punk", "punk", "Q3071"),
        ("blues", "blues", "Q9759"),
        ("reggae", "reggae", "Q9794"),
        ("folk", "folk", "Q43343"),
        ("rnb", "R&B", "Q45981"),
        ("funk", "funk", "Q164444"),
        ("disco", "disco", "Q58339"),
        ("indie", "indie rock", "Q183504"),
        ("alternative", "alternative rock", "Q11366"),
        ("kpop", "K-pop", "Q213665"),
        ("soul", "soul", "Q131272"),
    ]
    templates = []
    for slug, label, qid in genres:
        patterns = f"?item wdt:P31 wd:Q215380 . ?item wdt:P136 wd:{qid} ."
        templates.append(_simple(f"band-{slug}", f"Name a {label} band", "music", patterns, 12, 80))
    return templates


def _cities() -> list[Template]:
    countries = [
        ("us", "the United States", "Q30"),
        ("india", "India", "Q668"),
        ("china", "China", "Q148"),
        ("brazil", "Brazil", "Q155"),
        ("russia", "Russia", "Q159"),
        ("japan", "Japan", "Q17"),
        ("mexico", "Mexico", "Q96"),
        ("germany", "Germany", "Q183"),
        ("indonesia", "Indonesia", "Q252"),
        ("uk", "the United Kingdom", "Q145"),
        ("france", "France", "Q142"),
        ("nigeria", "Nigeria", "Q1033"),
        ("pakistan", "Pakistan", "Q843"),
        ("bangladesh", "Bangladesh", "Q902"),
        ("philippines", "the Philippines", "Q928"),
        ("turkey", "Turkey", "Q43"),
        ("iran", "Iran", "Q794"),
        ("egypt", "Egypt", "Q79"),
        ("italy", "Italy", "Q38"),
        ("spain", "Spain", "Q29"),
        ("canada", "Canada", "Q16"),
        ("australia", "Australia", "Q408"),
        ("argentina", "Argentina", "Q414"),
        ("south-africa", "South Africa", "Q258"),
        ("south-korea", "South Korea", "Q884"),
        ("colombia", "Colombia", "Q739"),
        ("poland", "Poland", "Q36"),
        ("thailand", "Thailand", "Q869"),
        ("vietnam", "Vietnam", "Q881"),
    ]
    templates = []
    for slug, label, qid in countries:
        patterns = f"?item wdt:P31 wd:Q515 . ?item wdt:P17 wd:{qid} ."
        # Include big cities and capitals, which are subclasses of city rather than P31 city.
        patterns = f"?item wdt:P17 wd:{qid} . ?item wdt:P31/wdt:P279* wd:Q515 ."
        templates.append(_simple(f"cities-{slug}", f"Name a city in {label}", "geography", patterns, 15, 60))
    return templates


def _years() -> list[Template]:
    templates = []
    specs = [
        ("film", "Name a film released in {year}", "film", "Q11424", "P577", range(1986, 2025), 8),
        ("game", "Name a video game released in {year}", "play", "Q7889", "P577", range(1991, 2025), 8),
        ("series", "Name a TV series that started in {year}", "film", "Q5398426", None, range(1998, 2025), 8),
        ("album", "Name an album released in {year}", "music", "Q482994", "P577", range(2004, 2025), 8),
    ]
    for prefix, text, category, qid, prop, years, minimum in specs:
        for year in years:
            if prop:
                # Ignore later reissues. The first publication year is the one that counts.
                patterns = f"""?item wdt:P31 wd:{qid} . ?item wdt:{prop} ?date .
FILTER(YEAR(?date) = {year})
FILTER NOT EXISTS {{ ?item wdt:{prop} ?earlier . FILTER(YEAR(?earlier) < {year}) }}"""
            else:
                # Start time only. Adding inception as a second branch makes this query time out.
                patterns = f"""?item wdt:P31 wd:{qid} . ?item wdt:P580 ?date .
FILTER(YEAR(?date) = {year})
FILTER NOT EXISTS {{ ?item wdt:P580 ?earlier . FILTER(YEAR(?earlier) < {year}) }}"""
            templates.append(_simple(
                f"{prefix}-{year}",
                text.format(year=year),
                category,
                patterns,
                minimum,
                90,
            ))
    return templates
