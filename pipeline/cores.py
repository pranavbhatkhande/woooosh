"""Famous answers the bank itself must contain.

The judge is not a substitute for these. When cachybox is down the bank is the
only scorer, and it is also what assigns the tier. A household name that is
only a substring of some other entry (Anubis inside Hermanubis, Thor inside
Thor Girl) is missing: typing it scores nothing, or the model invents a tier.

Cores are inserted by hand into the common tier. A general-knowledge prompt
whose required name is still absent after that is dropped.
"""

from __future__ import annotations

from pipeline.normalize import normalize

# Full answer names. Each one must exist as its own entry, not merely as a
# token inside a longer title. Missing names are added; they are not left for
# the judge.
CORES: dict[str, tuple[str, ...]] = {
    "wd-gk-god-egypt": ("Anubis", "Isis", "Osiris", "Horus", "Ra", "Thoth", "Seth"),
    "wd-gk-god-greek": (
        "Zeus",
        "Hera",
        "Poseidon",
        "Athena",
        "Apollo",
        "Artemis",
        "Ares",
        "Aphrodite",
        "Hermes",
        "Hephaestus",
        "Demeter",
        "Hestia",
        "Hades",
        "Dionysus",
    ),
    "wd-gk-god-roman": (
        "Jupiter",
        "Juno",
        "Neptune",
        "Mars",
        "Venus",
        "Minerva",
        "Mercury",
        "Apollo",
        "Diana",
        "Vulcan",
        "Pluto",
        "Bacchus",
    ),
    "wd-gk-kami": ("Amaterasu", "Susanoo", "Izanagi", "Izanami", "Inari"),
    "wd-gk-marvel": ("Spider-Man", "Iron Man", "Captain America", "Thor", "Hulk", "Wolverine"),
    "wd-gk-dc": ("Batman", "Superman", "Wonder Woman", "Aquaman", "Flash"),
    "wd-gk-jazz": (
        "Louis Armstrong",
        "Miles Davis",
        "Duke Ellington",
        "John Coltrane",
        "Charlie Parker",
        "Ella Fitzgerald",
    ),
    "wd-gk-bball": ("Michael Jordan", "LeBron James", "Kobe Bryant", "Magic Johnson"),
    "wd-gk-lang-in": (
        "Hindi",
        "Bengali",
        "Tamil",
        "Telugu",
        "Urdu",
        "Marathi",
        "Malayalam",
        "Kannada",
        "Punjabi",
        "Odia",
        "Gujarati",
        "Sanskrit",
    ),
    "wd-gk-fast-dish": ("hamburger", "pizza", "hot dog", "fries", "taco"),
    "wd-gk-bird": ("Eagle", "Penguin", "bald eagle", "House Sparrow"),
    "wd-gk-disney-char": ("Mickey Mouse", "Donald Duck", "Goofy"),
    "wd-gk-nintendo-fr": ("Mario", "The Legend of Zelda", "Pokémon"),
    "wd-gk-volc-active": ("Kīlauea", "Mount Vesuvius", "Mount Etna", "Mount Fuji"),
    "wd-gk-anime": ("Naruto", "One Piece", "Dragon Ball", "Attack on Titan", "Sailor Moon"),
    "wd-gk-rock-us": ("Bruce Springsteen", "Chuck Berry", "Jimi Hendrix", "Elvis Presley"),
    "wd-gk-social": ("Facebook", "Instagram", "YouTube", "TikTok", "Twitter", "Reddit", "LinkedIn"),
    "wd-gk-soul": ("Aretha Franklin", "Marvin Gaye", "Stevie Wonder", "Otis Redding", "James Brown"),
    "wd-gk-novel-uk": ("George Orwell", "Virginia Woolf", "Agatha Christie", "J. R. R. Tolkien"),
    "wd-gk-poet-uk": (
        "John Keats",
        "William Shakespeare",
        "William Wordsworth",
        "Lord Byron",
        "William Blake",
    ),
    "wd-gk-chef": ("Emeril Lagasse", "Julia Child", "Anthony Bourdain"),
    "wd-gk-astronaut": ("Neil Armstrong", "Buzz Aldrin", "Sally Ride"),
    "wd-gk-inventor": ("Thomas Edison", "Nikola Tesla", "Benjamin Franklin"),
    "wd-gk-physicist": ("Richard Feynman", "Albert Einstein", "J. Robert Oppenheimer"),
    "wd-gk-fabric": ("Cotton", "silk", "Denim", "linen"),
    "wd-gk-film-action": ("The Terminator", "Die Hard", "Mad Max", "John Wick"),
    "wd-gk-film-comedy-us": ("Groundhog Day", "Ghostbusters", "Airplane!", "Superbad"),
    "wd-gk-film-crime": ("Goodfellas", "The Godfather", "Pulp Fiction", "Scarface"),
    "wd-gk-film-drama": ("The Godfather", "Forrest Gump", "Schindler's List", "The Shawshank Redemption"),
    "wd-gk-film-drama-uk": ("Lawrence of Arabia", "The King's Speech", "Brief Encounter"),
    "wd-gk-furniture": ("Sofa", "Chair", "Table", "Bed"),
    "wd-gk-bread": ("Baguette", "Sourdough", "Pita", "Brioche"),
    "wd-gk-cake": ("Cheesecake", "Chocolate cake", "Carrot cake"),
    "wd-gk-disease": ("Malaria", "Influenza", "Tuberculosis", "Measles"),
    "wd-gk-genre-music": ("Reggae", "Jazz", "Rock", "Hip hop", "Blues"),
    "wd-gk-salad": ("Caesar salad", "Greek salad", "Cobb salad"),
    "wd-gk-singer-uk": ("David Bowie", "Elton John", "Paul McCartney"),
    "wd-gk-singer-us": ("Frank Sinatra", "Elvis Presley", "Michael Jackson", "Beyoncé"),
    "wd-gk-franchise": ("Star Wars", "Harry Potter", "Marvel"),
    "wd-gk-alkaloid": ("Caffeine", "Nicotine", "Morphine"),
    "wd-gk-architect": ("Frank Lloyd Wright",),
    "wd-gk-explorer": ("Christopher Columbus", "Leif Erikson"),
    "wd-gk-club-fr": ("Olympique de Marseille", "Paris Saint-Germain"),
    "wd-gk-club-tr": ("Galatasaray", "Fenerbahçe"),
    "wd-gk-club-fi": ("HJK Helsinki",),
    "wd-gk-club-rs": ("Red Star Belgrade",),
    "wd-gk-city-it-laz": ("Rome",),
    "wd-gk-city-dz": ("Algiers",),
    "wd-gk-city-no": ("Bergen", "Oslo"),
    "wd-gk-mtn-it": ("Mount Etna",),
    "wd-gk-mtn-wa": ("Mount Rainier",),
    "wd-gk-mtn-kr": ("Hallasan",),
    "wd-gk-isle-in": ("Andaman Islands",),
}

# Short names players actually type, attached to the longer page that is already in the bank.
ALIASES: dict[str, tuple[tuple[str, str], ...]] = {
    "wd-gk-heritage-fr": (("Palace of Versailles", "Versailles"),),
    "wd-gk-park-ny": (
        ("Letchworth State Park", "Letchworth"),
        ("Niagara Falls State Park", "Niagara Falls"),
    ),
    "wd-gk-park-fl": (("Bahia Honda Key", "Bahia Honda"),),
    "wd-gk-club-rs": (("Red Star Belgrade", "Red Star"),),
    "wd-gk-film-comedy-us": (("Groundhog Day", "Groundhog"),),
    "wd-gk-film-drama-uk": (("Lawrence of Arabia", "Lawrence"),),
}

# Pages that crawled into the common tier and are not answers to the prompt.
REJECT: dict[str, tuple[str, ...]] = {
    "wd-gk-god-greek": ("Homer", "Lycurgus of Sparta"),
    "wd-gk-kami": ("kami",),
    "wd-gk-poet-uk": ("metaphysical poets",),
    "wd-gk-social": ("social networking service",),
    "wd-gk-fast-dish": ("fast food", "junk food"),
    "wd-gk-genre-music": ("music genre",),
    "wd-gk-furniture": ("furniture",),
    "wd-gk-alkaloid": ("alkaloid",),
    "wd-gk-disease": ("social distancing", "pathogen"),
    "wd-gk-bread": ("bread machine", "baker's yeast", "bread crumbs"),
    "wd-gk-lang-in": (
        "languages of India",
        "Languages with official status in India",
        "Bangla alphabet",
        "World Sanskrit Conference",
    ),
}


def token_present(answers: list[dict], expected: str) -> bool:
    """True when the expected name is a whole token, not a piece of another word.

    Ferencvárosi still counts for Ferencvaros. Hermanubis does not count for Anubis.
    """
    needle = normalize(expected)
    if not needle:
        return False
    nparts = needle.split()
    for answer in answers:
        texts = [answer.get("name") or ""]
        texts.extend(answer.get("aliases") or [])
        for text in texts:
            folded = normalize(text)
            parts = folded.split()
            if not parts:
                continue
            if len(nparts) == 1:
                if needle in parts:
                    return True
                if any(part.startswith(needle) and 0 < len(part) - len(needle) <= 2 for part in parts):
                    return True
            else:
                width = len(nparts)
                for index in range(len(parts) - width + 1):
                    if parts[index : index + width] == nparts:
                        return True
    return False


def _named(answers: list[dict], key: str) -> bool:
    """An alias is not the answer. Thor Girl's alias Thor still needs an entry named Thor."""
    return any(normalize(answer.get("name") or "") == key for answer in answers)


def ensure_cores(prompt: dict) -> dict:
    """Copy the prompt, drop rejected titles, and insert any missing core names."""
    prompt_id = str(prompt.get("id") or "")
    answers = []
    for answer in prompt.get("answers") or []:
        answers.append({**answer, "aliases": list(answer.get("aliases") or [])})
    rejected = {normalize(name) for name in REJECT.get(prompt_id, ())}
    if rejected:
        answers = [answer for answer in answers if normalize(answer.get("name") or "") not in rejected]
    added: list[str] = []
    for name in CORES.get(prompt_id, ()):
        key = normalize(name)
        if not key or _named(answers, key):
            continue
        for answer in answers:
            answer["aliases"] = [alias for alias in answer["aliases"] if normalize(alias) != key]
        answers.append({"name": name, "aliases": [], "tier": "taxi", "gem": False})
        added.append(name)
    if added:
        print(f"add core {prompt_id}: {', '.join(added)}", flush=True)
    _attach_aliases(prompt_id, answers)
    return {**prompt, "answers": answers}


def _attach_aliases(prompt_id: str, answers: list[dict]) -> None:
    claimed: set[str] = set()
    by_name: dict[str, dict] = {}
    for answer in answers:
        key = normalize(answer.get("name") or "")
        if key:
            claimed.add(key)
            by_name[key] = answer
        for alias in answer.get("aliases") or []:
            alias_key = normalize(alias)
            if alias_key:
                claimed.add(alias_key)
    for canonical, alias in ALIASES.get(prompt_id, ()):
        alias_key = normalize(alias)
        if not alias_key or alias_key in claimed:
            continue
        owner = by_name.get(normalize(canonical))
        if owner is None:
            answers.append({"name": alias, "aliases": [], "tier": "taxi", "gem": False})
        else:
            owner["aliases"] = [*(owner.get("aliases") or []), alias]
        claimed.add(alias_key)


def apply_known_cores(prompts: dict[str, dict]) -> dict[str, dict]:
    """Insert cores, then drop a new general-knowledge prompt that still lacks its must-name."""
    from pipeline.jobs import all_jobs
    from pipeline.quality import lint_prompt

    musts = {job["id"]: list(job.get("must") or []) for job in all_jobs()}
    kept: dict[str, dict] = {}
    for prompt_id, prompt in prompts.items():
        fixed = ensure_cores(prompt)
        if str(prompt_id).startswith("wd-gk-"):
            gap = [name for name in musts.get(prompt_id, []) if not token_present(fixed.get("answers") or [], name)]
            if gap:
                print(
                    f"drop missing core {prompt_id}: {', '.join(gap)} ({fixed.get('text')})",
                    flush=True,
                )
                continue
        errors = lint_prompt(fixed)
        if errors:
            print(f"drop {prompt_id} after cores: {errors[0]}", flush=True)
            continue
        kept[prompt_id] = fixed
    return kept
