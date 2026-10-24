"""Prompts an average American adult can answer, and US familiarity order.

A name from the hand list is the famous core: it has to exist, and it sits in
the common tiers. Harvested category members fill the rest of the bank so a
real answer still scores when the judge is down. Closed sets (states,
presidents, holidays, the current leagues) stay complete instead of being padded.
"""

from __future__ import annotations

import re

from pipeline.normalize import keys_for, normalize
from pipeline.quality import lint_prompt
from pipeline.tiers import TIER_ORDER, pick_gem, tier_for_rarity

# Live deck. Anything else is dropped at publish and is not regenerated weekly.
KEEP = frozenset(
    {
        # US cities already in the bank, plus the full California set.
        "wd-city-al", "wd-city-az", "wd-city-co", "wd-city-ct", "wd-city-fl", "wd-city-ga",
        "wd-city-il", "wd-city-in", "wd-city-ky", "wd-city-la", "wd-city-ma", "wd-city-md",
        "wd-city-mi", "wd-city-mn", "wd-city-mo", "wd-city-nc", "wd-city-nj", "wd-city-nv",
        "wd-city-ny", "wd-city-oh", "wd-city-or", "wd-city-pa", "wd-city-tn", "wd-city-ut",
        "wd-city-va", "wd-city-wa", "wd-city-wi",
        "wd-gk-city-ak", "wd-gk-city-ar", "wd-gk-city-ia", "wd-gk-city-id", "wd-gk-city-ks",
        "wd-gk-city-nd", "wd-gk-city-ne", "wd-gk-city-ok", "wd-gk-city-sd", "wd-gk-city-tx",
        "cur-city-ca",
        "wd-us-state", "wd-president", "wd-country", "cur-capital",
        # Sports Americans can name cold.
        "wd-clubs-premier", "cur-nfl", "cur-nba", "cur-mlb", "cur-sport",
        "wd-gk-bball", "wd-gk-qb", "wd-gk-pitcher", "wd-gk-boxer-us", "wd-gk-golf-us",
        "wd-gk-tennis-us",
        # Movies, TV, music, games, kids.
        "wd-best-picture", "wd-disney", "wd-grammy-album", "wd-boyband", "wd-gk-grammy",
        "wd-gk-film-action", "wd-gk-film-comedy-us", "wd-gk-film-comedy-uk", "wd-gk-film-crime",
        "wd-gk-film-drama", "wd-gk-film-drama-uk", "wd-gk-film-genre", "wd-gk-film-horror",
        "wd-gk-broadway", "wd-gk-comic", "wd-gk-comic-strip", "wd-gk-marvel", "wd-gk-dc",
        "wd-gk-anime", "wd-gk-manga", "wd-gk-franchise", "wd-gk-franchise-game",
        "wd-gk-fps", "wd-gk-fighting", "wd-gk-rpg", "wd-gk-ps4", "wd-gk-windows", "wd-gk-ios",
        "wd-gk-studio", "wd-gk-game-genre", "wd-gk-singer-us", "wd-gk-singer-uk",
        "wd-gk-rock-us", "wd-gk-soul", "wd-gk-jazz", "wd-gk-genre-music",
        "wd-gk-actor-us-f", "wd-gk-actor-us-m", "wd-gk-actor-uk-f", "wd-gk-actor-uk-m",
        "wd-gk-novel-us", "wd-gk-novel-uk", "wd-gk-tv-genre",
        "cur-tv", "cur-channel", "cur-director", "cur-animated", "cur-starwars", "cur-potter",
        "cur-pokemon", "cur-simpsons", "cur-disney-char", "cur-game-char", "cur-holiday",
        # Animals, food, brands, everyday things.
        "wd-cat", "wd-dog", "wd-horse", "wd-gk-bird", "wd-gk-dino", "wd-gk-fish",
        "wd-element", "wd-car", "wd-sportscar", "wd-gk-ford", "wd-gk-toyota",
        "wd-gk-bread", "wd-gk-cake", "wd-gk-salad", "wd-gk-sauce", "wd-gk-hat", "wd-gk-fabric",
        "wd-gk-dish", "wd-gk-fast-dish", "wd-gk-icecream", "wd-gk-coffee-brand",
        "wd-gk-apple", "wd-gk-herb", "wd-gk-disease", "wd-gk-furniture", "wd-gk-social",
        "wd-gk-volc-active", "wd-gk-currency", "wd-gk-nobel-peace", "wd-gk-astronaut",
        "wd-gk-inventor", "wd-gk-chef", "wd-gk-star", "wd-gk-god-egypt", "wd-gk-god-greek",
        "cur-appliance", "cur-board", "cur-bone", "cur-breakfast", "cur-candy", "cur-cards",
        "cur-cheese", "cur-clothing", "cur-cocktail", "cur-color", "cur-dance", "cur-fastfood",
        "cur-flower", "cur-fruit", "cur-gemstone", "cur-greek", "cur-instrument", "cur-park",
        "cur-pasta", "cur-sea", "cur-soda", "cur-spice", "cur-tool", "cur-tree",
        "cur-vegetable", "cur-weather", "cur-cereal", "cur-snack", "cur-clothes-brand",
    }
)

# Names Americans say first. Missing ones are inserted; buried ones move to taxi.
HOUSEHOLD: dict[str, tuple[str, ...]] = {
    "cur-park": (
        "Yellowstone", "Yosemite", "Grand Canyon", "Zion", "Glacier", "Acadia",
        "Rocky Mountain", "Great Smoky Mountains", "Everglades", "Grand Teton",
        "Arches", "Bryce Canyon", "Joshua Tree", "Death Valley", "Sequoia",
        "Denali", "Crater Lake", "Mount Rainier", "Hot Springs", "Olympic",
    ),
    "cur-flower": (
        "Rose", "Tulip", "Daisy", "Sunflower", "Lily", "Daffodil", "Carnation",
        "Orchid", "Iris", "Violet", "Marigold", "Peony", "Hydrangea",
    ),
    "cur-tree": (
        "Oak", "Pine", "Maple", "Birch", "Willow", "Palm", "Redwood", "Cedar",
        "Spruce", "Elm", "Cherry",
    ),
    "cur-spice": (
        "Cinnamon", "Black pepper", "Paprika", "Oregano", "Nutmeg", "Ginger",
        "Garlic", "Cumin", "Salt", "Vanilla",
    ),
    "cur-vegetable": ("Carrot", "Potato", "Onion", "Tomato", "Broccoli", "Corn", "Lettuce", "Spinach"),
    "wd-gk-herb": ("Basil", "Parsley", "Oregano", "Rosemary", "Thyme", "Cilantro", "Mint", "Dill", "Sage"),
    "wd-gk-apple": ("Granny Smith", "Honeycrisp", "Gala", "Fuji", "Red Delicious", "Golden Delicious", "McIntosh"),
    "wd-gk-film-horror": (
        "Halloween", "Friday the 13th", "A Nightmare on Elm Street", "Scream",
        "The Exorcist", "Get Out", "The Shining", "Psycho", "The Conjuring",
        "A Quiet Place", "Child's Play", "Poltergeist", "The Blair Witch Project",
        "Carrie", "Jaws",
    ),
    "wd-gk-singer-us": (
        "Taylor Swift", "Beyoncé", "Elvis Presley", "Michael Jackson", "Madonna",
        "Whitney Houston", "Billie Eilish", "Ariana Grande", "Britney Spears",
        "Mariah Carey", "Jennifer Lopez", "Bruno Mars", "Lady Gaga", "Eminem",
    ),
    "wd-gk-grammy": (
        "Taylor Swift", "Beyoncé", "Adele", "Michael Jackson", "The Beatles",
        "Elvis Presley", "Whitney Houston", "Madonna", "Billie Eilish", "Bruno Mars",
        "Eminem", "Stevie Wonder",
    ),
    "wd-gk-anime": (
        "Pokémon", "Dragon Ball", "Naruto", "One Piece", "Attack on Titan",
        "Demon Slayer", "Sailor Moon", "My Hero Academia", "Death Note",
        "Fullmetal Alchemist", "Cowboy Bebop",
    ),
    "wd-gk-fps": (
        "Halo", "Call of Duty", "Doom", "Counter-Strike", "Overwatch", "Half-Life",
        "BioShock", "Battlefield", "Valorant", "Left 4 Dead",
    ),
    "wd-gk-fighting": ("Street Fighter", "Mortal Kombat", "Tekken", "Super Smash Bros.", "Soulcalibur"),
    "cur-board": ("Monopoly", "Scrabble", "Clue", "Candy Land", "Risk", "Jenga", "Sorry!", "Battleship"),
    "cur-soda": ("Coca-Cola", "Pepsi", "Sprite", "Dr Pepper", "Mountain Dew", "7 Up", "Fanta"),
    "wd-gk-social": ("Facebook", "Instagram", "Twitter", "TikTok", "Snapchat", "YouTube", "Reddit", "Pinterest", "WhatsApp"),
    "wd-gk-bird": ("Eagle", "Bald eagle", "Blue jay", "Cardinal", "Robin", "Owl", "Penguin", "Crow", "Hawk", "Parrot", "Flamingo"),
    "wd-disney": (
        "The Lion King", "Frozen", "Snow White and the Seven Dwarfs", "Aladdin",
        "Beauty and the Beast", "Moana", "Encanto", "Bambi", "Cinderella",
        "Pinocchio", "The Little Mermaid", "Mulan",
    ),
    "wd-gk-disease": ("Influenza", "Common cold", "COVID-19", "Measles", "Chickenpox", "Tuberculosis"),
    "wd-gk-astronaut": ("Neil Armstrong", "Buzz Aldrin", "John Glenn", "Sally Ride", "Alan Shepard"),
    "wd-gk-rock-us": ("Elvis Presley", "Bruce Springsteen", "Chuck Berry", "Jimi Hendrix", "Johnny Cash", "Bob Dylan"),
    "wd-gk-soul": ("Aretha Franklin", "Marvin Gaye", "Stevie Wonder", "James Brown", "Otis Redding", "Sam Cooke"),
    "wd-gk-novel-uk": ("J. K. Rowling", "C. S. Lewis", "Roald Dahl", "Jane Austen", "Charles Dickens", "George Orwell", "Agatha Christie"),
    "wd-gk-chef": ("Julia Child", "Emeril Lagasse", "Bobby Flay", "Guy Fieri", "Ina Garten", "Anthony Bourdain", "Rachael Ray"),
    "wd-gk-inventor": ("Thomas Edison", "Benjamin Franklin", "Alexander Graham Bell", "Orville Wright", "Wilbur Wright", "Nikola Tesla"),
    "cur-bone": ("Skull", "Rib", "Spine", "Femur", "Pelvis", "Kneecap"),
    "cur-candy": ("M&M's", "Snickers", "Reese's", "Skittles", "Kit Kat", "Twix", "Hershey's", "Starburst"),
}

LATIN_IDS = frozenset(
    {"cur-flower", "cur-tree", "cur-spice", "cur-vegetable", "wd-gk-herb", "wd-gk-apple"}
)
_GENUS = frozenset(
    {"rosa", "morus", "pyrus", "mentha", "paeonia", "quercus", "pinus", "allium", "malus", "foeniculum"}
)
_ENGLISH_FIRST = frozenset(
    {
        "european", "common", "northern", "southern", "american", "african", "asian",
        "red", "blue", "black", "white", "green", "golden", "house", "greater",
        "lesser", "date", "wild", "sweet", "hot", "yellow", "little", "big",
        "western", "eastern", "mountain", "sea", "cherry", "grape", "bell",
    }
)
_BINOMIAL = re.compile(r"\b[A-Z][a-z]{2,} [a-z]{4,}\b")
_TIER_RANK = {name: index for index, name in enumerate(TIER_ORDER)}


def kept_prompt(prompt_id: str) -> bool:
    return prompt_id in KEEP


def looks_latin(name: str) -> bool:
    if normalize(name) in _GENUS:
        return True
    match = _BINOMIAL.search(name or "")
    if not match:
        return False
    first = match.group(0).split()[0].lower()
    return first not in _ENGLISH_FIRST


def _copy_answers(prompt: dict) -> list[dict]:
    copied = []
    for answer in prompt.get("answers") or []:
        copied.append({**answer, "aliases": list(answer.get("aliases") or [])})
    return copied


def _index_answers(answers: list[dict]) -> dict[str, dict]:
    by: dict[str, dict] = {}
    for answer in answers:
        key = normalize(answer.get("name") or "")
        if key:
            by.setdefault(key, answer)
    return by


def _ensure_named(answers: list[dict], by: dict[str, dict], name: str, aliases: list[str] | None = None) -> dict:
    """Find a name even when the bank spells it with a space, and never insert a second one."""
    key = normalize(name)
    wanted = keys_for(name, [])
    found = by.get(key)
    if found is None:
        for answer in answers:
            if wanted & keys_for(answer.get("name") or "", answer.get("aliases") or []):
                found = answer
                break
    if found is None:
        for answer in answers:
            if _covers(answer.get("name") or "", key):
                found = answer
                break
    if found is None:
        for answer in answers:
            answer["aliases"] = [alias for alias in answer["aliases"] if not (keys_for(alias, []) & wanted)]
        found = {"name": name, "aliases": [], "tier": "taxi", "gem": False, "pop": 0, "sitelinks": 0, "qid": None}
        answers.append(found)
        by[key] = found
    elif normalize(found.get("name") or "") != key:
        found["name"] = name
        found["aliases"] = [alias for alias in found["aliases"] if not (keys_for(alias, []) & wanted)]
        by[key] = found
    claimed = keys_for(found["name"], found["aliases"])
    for alias in aliases or []:
        alias_keys = keys_for(alias, [])
        if not alias_keys or alias_keys & claimed:
            continue
        if any(alias_keys & keys_for(answer.get("name") or "", answer.get("aliases") or []) for answer in answers if answer is not found):
            continue
        found["aliases"].append(alias)
        claimed.update(alias_keys)
    return found


def _covers(hay: str, key: str) -> bool:
    """A longer page title still counts when it leads with the familiar name."""
    parts = key.split()
    if len(parts) < 2:
        return False
    words = normalize(hay).split()
    return words[: len(parts)] == parts


def _fill_tiers(answers: list[dict], protected: set[int]) -> None:
    present = {answer.get("tier") for answer in answers}
    for tier in ("taxi", "climb", "burn", "stall", "apogee"):
        if tier in present:
            continue
        donors = [
            answer
            for answer in answers
            if not answer.get("gem") and id(answer) not in protected and answer.get("tier") != "escape"
        ]
        if len(donors) < 2:
            donors = [answer for answer in answers if not answer.get("gem")]
        if len(donors) < 2:
            return
        counts: dict[str, int] = {}
        for answer in donors:
            counts[answer.get("tier") or ""] = counts.get(answer.get("tier") or "", 0) + 1
        donor_tier = max(counts, key=counts.get)
        if counts[donor_tier] <= 1:
            return
        for answer in answers:
            if answer.get("tier") == donor_tier and not answer.get("gem") and id(answer) not in protected:
                answer["tier"] = tier
                present.add(tier)
                break


def _one_gem(answers: list[dict], prefer: dict | None = None) -> None:
    gem = prefer if prefer is not None and prefer in answers else next((answer for answer in answers if answer.get("gem")), None)
    if gem is None and answers:
        gem = answers[-1]
    for answer in answers:
        if answer is gem:
            answer["gem"] = True
            answer["tier"] = "escape"
        else:
            answer["gem"] = False
            if answer.get("tier") == "escape":
                answer["tier"] = "apogee"


def pin_hand_order(prompt: dict, hand_entries: list[dict]) -> dict:
    """Put the hand list first, then the harvested tail, and tier that order."""
    answers = _copy_answers(prompt)
    by = _index_answers(answers)
    core: list[dict] = []
    seen: set[int] = set()
    for entry in hand_entries:
        found = _ensure_named(answers, by, entry["name"], entry.get("aliases") or [])
        if id(found) in seen:
            continue
        seen.add(id(found))
        core.append(found)
        by = _index_answers(answers)
    rest = [answer for answer in answers if id(answer) not in seen]
    # Within a popularity tier, keep the more familiar names ahead so the
    # rarity index is not just alphabetical.
    rest.sort(
        key=lambda answer: (
            _TIER_RANK.get(answer.get("tier"), 9),
            -float(answer.get("pop") or 0),
            -int(answer.get("sitelinks") or 0),
            (answer.get("name") or "").lower(),
        )
    )
    ordered = core + rest
    last = max(1, len(ordered) - 1)
    for index, answer in enumerate(ordered):
        answer["rarity"] = index / last
        answer["tier"] = tier_for_rarity(index / last)
        answer["gem"] = False
        answer["sitelinks"] = int(answer.get("sitelinks") or 0)
    pool = [answer for answer in ordered if id(answer) not in {id(item) for item in core[:12]}] or ordered
    gem = pick_gem(pool)
    _one_gem(ordered, gem)
    _fill_tiers(ordered, {id(item) for item in core})
    return {**prompt, "answers": ordered}


def refresh_prompt(prompt: dict) -> dict:
    """Force household names onto taxi and move Latin heads out of the common tiers."""
    prompt_id = str(prompt.get("id") or "")
    names = HOUSEHOLD.get(prompt_id)
    if not names and prompt_id not in LATIN_IDS:
        return prompt
    answers = _copy_answers(prompt)
    by = _index_answers(answers)
    protected: set[int] = set()
    if names:
        for name in names:
            found = _ensure_named(answers, by, name)
            found["_household"] = True
            protected.add(id(found))
            by = _index_answers(answers)
    for answer in answers:
        if answer.get("_household") and not answer.get("gem"):
            answer["tier"] = "taxi"
    gem = next((answer for answer in answers if answer.get("gem")), None)
    if gem is None or gem.get("_household") or (prompt_id in LATIN_IDS and looks_latin(gem.get("name") or "")):
        pool = [
            answer
            for answer in answers
            if not answer.get("_household") and not (prompt_id in LATIN_IDS and looks_latin(answer.get("name") or ""))
        ]
        rank = {"apogee": 0, "stall": 1, "burn": 2, "climb": 3, "taxi": 4, "escape": 5}
        pool.sort(key=lambda answer: (rank.get(answer.get("tier"), 9), float(answer.get("pop") or 0), answer.get("name") or ""))
        if pool:
            if gem is not None and gem is not pool[0]:
                gem["gem"] = False
            gem = pool[0]
            gem["gem"] = True
            gem["tier"] = "escape"
    for answer in answers:
        if answer.get("_household") and answer is not gem:
            answer["tier"] = "taxi"
            answer["gem"] = False
    if prompt_id in LATIN_IDS:
        for answer in answers:
            if answer is gem or answer.get("_household"):
                continue
            if looks_latin(answer.get("name") or "") and answer.get("tier") in {"taxi", "climb", "burn"}:
                answer["tier"] = "apogee"
    _one_gem(answers, gem)
    _fill_tiers(answers, protected)
    for answer in answers:
        answer.pop("_household", None)
        answer.pop("rarity", None)
    return {**prompt, "answers": answers}


# Open sets must stay exhaustive. A 40-name hand list is only the famous core.
FULL_FLOOR = {
    "cur-pokemon": 800,
    "cur-starwars": 200,
    "cur-potter": 120,
    "cur-simpsons": 150,
    "cur-game-char": 200,
    "cur-animated": 200,
    "cur-director": 400,
    "cur-tv": 400,
    "cur-channel": 40,
    "cur-cereal": 80,
    "cur-snack": 80,
    "cur-clothes-brand": 150,
    "cur-disney-char": 200,
    "cur-city-ca": 150,
}


def apply_audience(prompts: dict[str, dict]) -> dict[str, dict]:
    """Drop prompts outside the American deck and retier the ones that stay."""
    kept: dict[str, dict] = {}
    short: list[str] = []
    for prompt_id, prompt in prompts.items():
        if prompt_id not in KEEP:
            print(f"drop audience {prompt_id}: {prompt.get('text')}", flush=True)
            continue
        fixed = refresh_prompt(prompt)
        errors = lint_prompt(fixed)
        if errors:
            print(f"drop audience lint {prompt_id}: {errors[0]}", flush=True)
            continue
        floor = FULL_FLOOR.get(prompt_id, 0)
        count = len(fixed.get("answers") or [])
        if count < floor:
            short.append(f"{prompt_id} {count}<{floor}")
        kept[prompt_id] = fixed
    missing = sorted(KEEP - set(kept))
    if missing:
        raise SystemExit("audience list missing from the bank: " + ", ".join(missing))
    if short:
        raise SystemExit("open sets are still a short sample: " + ", ".join(short))
    return kept
