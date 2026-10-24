"""Template catalog. Year slices use flat English Wikipedia categories.

A full-table SPARQL scan by year exceeds the public endpoint deadline, so the
candidate pool is every main-namespace page in the English Wikipedia category
(paginated category members, not a top-70 sample). Sitelink counts and English
aliases still come from Wikidata. Thin categories walk one level of subcategories.
"""

from __future__ import annotations


def _job(id_, text, category, kind, categories, **extra):
    job = {
        "id": id_,
        "text": text,
        "category": category,
        "kind": kind,
        "mode": "category",
        "categories": categories,
        "ban": extra.get("ban") or [],
        "must": extra.get("must") or [],
        "min_links": extra.get("min_links", 1),
    }
    for key in ("cap", "follow_subcats", "subcat_below", "places_from_subcats"):
        if extra.get(key) is not None:
            job[key] = extra[key]
    return job


def _years(kind, prefix, text, category_name, start, end, topic):
    jobs = []
    for year in range(end, start - 1, -1):
        jobs.append(
            _job(
                f"wd-{prefix}-{year}",
                text.format(year=year),
                topic,
                kind,
                [category_name.format(year=year)],
            )
        )
    return jobs


def _cities():
    # (id suffix, prompt, category title, a famous city that must survive ranking)
    rows = [
        ("fl", "Name a city in Florida", "Cities in Florida", "Miami"),
        ("oh", "Name a city in Ohio", "Cities in Ohio", "Columbus"),
        ("ny", "Name a city in New York state", "Cities in New York (state)", "New York"),
        ("il", "Name a city in Illinois", "Cities in Illinois", "Chicago"),
        ("pa", "Name a city in Pennsylvania", "Cities in Pennsylvania", "Philadelphia"),
        ("ma", "Name a city in Massachusetts", "Cities in Massachusetts", "Boston"),
        ("mi", "Name a city in Michigan", "Cities in Michigan", "Detroit"),
        ("az", "Name a city in Arizona", "Cities in Arizona", "Phoenix"),
        ("wa", "Name a city in Washington state", "Cities in Washington (state)", "Seattle"),
        ("co", "Name a city in Colorado", "Cities in Colorado", "Denver"),
        ("ga", "Name a city in the US state of Georgia", "Cities in Georgia (U.S. state)", "Atlanta"),
        ("nc", "Name a city in North Carolina", "Cities in North Carolina", "Charlotte"),
        ("va", "Name a city in Virginia", "Cities in Virginia", "Virginia Beach"),
        ("nj", "Name a city in New Jersey", "Cities in New Jersey", "Newark"),
        ("wi", "Name a city in Wisconsin", "Cities in Wisconsin", "Milwaukee"),
        ("mn", "Name a city in Minnesota", "Cities in Minnesota", "Minneapolis"),
        ("mo", "Name a city in Missouri", "Cities in Missouri", "St. Louis"),
        ("la", "Name a city in Louisiana", "Cities in Louisiana", "New Orleans"),
        ("or", "Name a city in Oregon", "Cities in Oregon", "Portland"),
        ("nv", "Name a city in Nevada", "Cities in Nevada", "Las Vegas"),
        ("tn", "Name a city in Tennessee", "Cities in Tennessee", "Nashville"),
        ("md", "Name a city in Maryland", "Cities in Maryland", "Baltimore"),
        ("in", "Name a city in Indiana", "Cities in Indiana", "Indianapolis"),
        ("ky", "Name a city in Kentucky", "Cities in Kentucky", "Louisville"),
        ("al", "Name a city in Alabama", "Cities in Alabama", "Birmingham"),
        ("ct", "Name a city in Connecticut", "Cities in Connecticut", "Hartford"),
        ("ut", "Name a city in Utah", "Cities in Utah", "Salt Lake City"),
    ]
    return [
        _job(
            f"wd-city-{code}",
            text,
            "geography",
            "place",
            [category],
            must=[must],
            ban=["list of", "metropolitan", "census"],
            places_from_subcats=True,
            subcat_below=40,
        )
        for code, text, category, must in rows
    ]


def specials():
    specs = [
        ("wd-clubs-premier", "Name a Premier League club", "sport", ["Premier League clubs"], ["Manchester United"], ["premier league"]),
        ("wd-clubs-laliga", "Name a La Liga club", "sport", ["La Liga clubs"], ["Barcelona"], ["la liga"]),
        ("wd-clubs-seriea", "Name a Serie A club", "sport", ["Serie A clubs"], ["Juventus"], ["serie a"]),
        ("wd-clubs-bundesliga", "Name a Bundesliga club", "sport", ["Bundesliga clubs"], ["Bayern"], ["bundesliga"]),
        ("wd-clubs-ligue1", "Name a Ligue 1 club", "sport", ["Ligue 1 clubs"], ["Paris Saint-Germain"], ["ligue 1"]),
        ("wd-kpop", "Name a K-pop group", "music", ["K-pop music groups"], ["BTS"], ["k-pop"]),
        ("wd-boyband", "Name an American boy band", "music", ["American boy bands"], ["Backstreet Boys"], []),
        ("wd-element", "Name a chemical element", "science", ["Chemical elements"], ["Oxygen", "Gold"], ["periodic table", "chemical element"]),
        ("wd-cat", "Name a cat breed", "nature", ["Cat breeds"], ["Siamese"], ["list of"]),
        ("wd-dog", "Name a dog breed", "nature", ["FCI breeds"], ["Labrador", "Beagle"], ["list of", "crossbreed"]),
        ("wd-horse", "Name a horse breed", "nature", ["Horse breeds"], ["Arabian"], ["list of"]),
        ("wd-opera", "Name an opera", "music", ["Operas"], ["Carmen"], ["list of operas"]),
        ("wd-nobel-physics", "Name a Nobel physics laureate", "science", ["Nobel laureates in Physics"], ["Albert Einstein"], ["nobel prize", "list of"]),
        ("wd-nobel-lit", "Name a Nobel literature laureate", "culture", ["Nobel laureates in Literature"], ["Bob Dylan"], ["nobel prize", "list of"]),
        ("wd-us-state", "Name a US state", "geography", ["States of the United States"], ["California", "Texas"], ["u.s. state", "united states"]),
        ("wd-president", "Name a US president", "culture", ["Presidents of the United States"], ["Abraham Lincoln"], ["president of", "first lady", "list of"]),
        ("wd-alps", "Name a mountain in the Alps", "geography", ["Mountains of the Alps"], ["Mont Blanc"], ["list of"]),
        ("wd-greek-island", "Name a Greek island", "geography", ["Islands of Greece"], ["Crete"], ["list of"]),
        ("wd-car", "Name a car brand", "culture", ["Car brands"], ["Toyota", "Ford"], ["list of"]),
        ("wd-sportscar", "Name a sports-car maker", "culture", ["Sports car manufacturers"], ["Ferrari", "Porsche"], ["list of"]),
        ("wd-jupiter-moon", "Name a moon of Jupiter", "science", ["Moons of Jupiter"], ["Europa", "Io"], ["moons of jupiter", "list of"]),
        ("wd-best-picture", "Name a Best Picture winner", "film", ["Best Picture Academy Award winners"], ["The Godfather"], ["academy award", "list of"]),
        ("wd-grammy-album", "Name an Album of the Year winner", "music", ["Grammy Award for Album of the Year"], ["Thriller"], ["grammy award", "list of"]),
        ("wd-alps-ca", "Name a mountain in California", "geography", ["Mountains of California"], ["Mount Whitney"], ["list of"]),
        ("wd-alps-co", "Name a mountain in Colorado", "geography", ["Mountains of Colorado"], ["Pikes Peak"], ["list of"]),
        ("wd-alps-jp", "Name a mountain in Japan", "geography", ["Mountains of Japan"], ["Mount Fuji"], ["list of"]),
        ("wd-alps-no", "Name a mountain in Norway", "geography", ["Mountains of Norway"], ["Galdhøpiggen"], ["list of"]),
        ("wd-isle-id", "Name an Indonesian island", "geography", ["Islands of Indonesia"], ["Java"], ["list of"]),
        ("wd-isle-jp", "Name a Japanese island", "geography", ["Islands of Japan"], ["Honshu"], ["list of"]),
        ("wd-isle-scot", "Name a Scottish island", "geography", ["Islands of Scotland"], ["Skye"], ["list of"]),
        ("wd-isle-ph", "Name a Philippine island", "geography", ["Islands of the Philippines"], ["Luzon"], ["list of"]),
        ("wd-volcano-jp", "Name a volcano in Japan", "geography", ["Volcanoes of Japan"], ["Mount Fuji"], ["list of"]),
        ("wd-volcano-it", "Name a volcano in Italy", "geography", ["Volcanoes of Italy"], ["Vesuvius"], ["list of"]),
        ("wd-lake-fi", "Name a lake in Finland", "geography", ["Lakes of Finland"], ["Saimaa"], ["list of"]),
        ("wd-castle-de", "Name a castle in Germany", "culture", ["Castles in Germany"], ["Neuschwanstein"], ["list of"]),
        ("wd-castle-scot", "Name a castle in Scotland", "culture", ["Castles in Scotland"], ["Edinburgh Castle"], ["list of"]),
        ("wd-disney", "Name a Disney animated film", "film", ["Walt Disney Animation Studios films"], ["The Lion King"], ["list of"]),
        ("wd-ghibli", "Name a Studio Ghibli film", "film", ["Studio Ghibli films"], ["Spirited Away"], ["list of"]),
        ("wd-bond", "Name a James Bond film", "film", ["James Bond films"], ["Goldfinger"], ["list of"]),
    ]
    jobs = []
    for id_, text, topic, cats, must, ban in specs:
        jobs.append(_job(id_, text, topic, "special", cats, must=must, ban=ban))
    return jobs


def sparql_jobs():
    return [
        {
            "id": "wd-country",
            "text": "Name a country",
            "category": "geography",
            "kind": "closed",
            "mode": "sparql",
            "min_links": 12,
            "must": ["France", "Japan", "Brazil"],
            "ban": ["list of"],
            "query": """
            SELECT ?item ?itemLabel ?sitelinks WHERE {
              ?item wdt:P31 wd:Q3624078 ;
                    wikibase:sitelinks ?sitelinks ;
                    rdfs:label ?itemLabel .
              FILTER(LANG(?itemLabel)="en")
              FILTER(?sitelinks >= 15)
              FILTER NOT EXISTS { ?item wdt:P576 ?ended }
            }
            LIMIT 240
            """,
        },
    ]


def all_jobs():
    jobs = []
    jobs.extend(_years("film", "film", "Name a film released in {year}", "{year} films", 1976, 2025, "film"))
    jobs.extend(_years("game", "game", "Name a video game released in {year}", "{year} video games", 1992, 2025, "game"))
    jobs.extend(_years("album", "album", "Name an album released in {year}", "{year} albums", 1972, 2024, "music"))
    jobs.extend(
        _years(
            "tv",
            "tv",
            "Name a TV series that premiered in {year}",
            "{year} American television series debuts",
            1992,
            2024,
            "tv",
        )
    )
    jobs.extend(
        _years(
            "tvuk",
            "tvuk",
            "Name a British TV series that premiered in {year}",
            "{year} British television series debuts",
            2000,
            2024,
            "tv",
        )
    )
    jobs.extend(_cities())
    jobs.extend(specials())
    jobs.extend(sparql_jobs())
    return jobs


def iter_jobs():
    """Round-robin across kinds so a partial run stays varied."""
    buckets: dict[str, list] = {}
    for job in all_jobs():
        buckets.setdefault(job["kind"], []).append(job)
    order = ["film", "game", "album", "tv", "special", "place", "tvuk", "closed"]
    while any(buckets.values()):
        for kind in order:
            if buckets.get(kind):
                yield buckets[kind].pop(0)
        for kind in list(buckets):
            if kind not in order and buckets[kind]:
                yield buckets[kind].pop(0)
