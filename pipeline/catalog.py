"""General-knowledge jobs.

Geography with a few hundred or a couple thousand pages uses every category
member, then sitelink rank. People, works, and other huge categories use
incoming-link search so famous answers are in the slice and one prompt stays
under the shard cap. Nothing here is pinned to a release year.
"""

from __future__ import annotations

LINK_CAP = 1200
ANSWER_CAP = 1800

# Confirmed large enough to collect in full (English Wikipedia page counts).
_US_CITIES = [
    ("tx", "Name a city in Texas", "Cities in Texas", "Houston"),
    ("ia", "Name a city in Iowa", "Cities in Iowa", "Des Moines"),
    ("ks", "Name a city in Kansas", "Cities in Kansas", "Wichita"),
    ("ar", "Name a city in Arkansas", "Cities in Arkansas", "Little Rock"),
    ("id", "Name a city in Idaho", "Cities in Idaho", "Boise"),
    ("ok", "Name a city in Oklahoma", "Cities in Oklahoma", "Oklahoma City"),
    ("sd", "Name a city in South Dakota", "Cities in South Dakota", "Sioux Falls"),
    ("ne", "Name a city in Nebraska", "Cities in Nebraska", "Omaha"),
    ("ak", "Name a city in Alaska", "Cities in Alaska", "Anchorage"),
    ("nd", "Name a city in North Dakota", "Cities in North Dakota", "Fargo"),
]

_REGION_CITIES = [
    ("ch", "Name a city in Switzerland", "Cities in Switzerland", "Zurich"),
    ("ng", "Name a city in Nigeria", "Cities in Nigeria", "Lagos"),
    ("eg", "Name a city in Egypt", "Cities in Egypt", "Cairo"),
    ("nl", "Name a city in the Netherlands", "Cities in the Netherlands", "Amsterdam"),
    ("dz", "Name a city in Algeria", "Cities in Algeria", "Algiers"),
    ("hr", "Name a city in Croatia", "Cities and towns in Croatia", "Zagreb"),
    ("cl", "Name a city in Chile", "Communes of Chile", "Santiago"),
    ("it-lom", "Name a city in Lombardy", "Cities and towns in Lombardy", "Milan"),
    ("it-pie", "Name a city in Piedmont", "Cities and towns in Piedmont", "Turin"),
    ("it-ven", "Name a city in Veneto", "Cities and towns in Veneto", "Venice"),
    ("it-cam", "Name a city in Campania", "Cities and towns in Campania", "Naples"),
    ("it-sic", "Name a city in Sicily", "Cities and towns in Sicily", "Palermo"),
    ("it-cal", "Name a city in Calabria", "Cities and towns in Calabria", "Reggio"),
    ("it-sar", "Name a city in Sardinia", "Cities and towns in Sardinia", "Cagliari"),
    ("it-emi", "Name a city in Emilia-Romagna", "Cities and towns in Emilia-Romagna", "Bologna"),
    ("it-laz", "Name a city in Lazio", "Cities and towns in Lazio", "Rome"),
    ("it-tus", "Name a city in Tuscany", "Cities and towns in Tuscany", "Florence"),
    ("it-abr", "Name a city in Abruzzo", "Cities and towns in Abruzzo", "Pescara"),
    ("it-apu", "Name a city in Apulia", "Cities and towns in Apulia", "Bari"),
    ("it-lig", "Name a city in Liguria", "Cities and towns in Liguria", "Genoa"),
    ("it-mar", "Name a city in Marche", "Cities and towns in Marche", "Ancona"),
    ("it-fri", "Name a city in Friuli", "Cities and towns in Friuli-Venezia Giulia", "Trieste"),
    ("no", "Name a city in Norway", "Cities and towns in Norway", "Bergen"),
    ("dk", "Name a city in Denmark", "Municipalities of Denmark", "Copenhagen"),
]

# Most "Cities in X" titles are indexes of a few dozen pages. These two are member lists.
_COUNTRY_CITIES = [
    ("pt", "Name a city in Portugal", "Cities in Portugal", "Lisbon"),
    ("ro", "Name a city in Romania", "Cities in Romania", "Bucharest"),
]

_CLUBS = [
    ("de", "Name a German football club", "Football clubs in Germany", "Bayern"),
    ("no", "Name a Norwegian football club", "Football clubs in Norway", "Rosenborg"),
    ("it", "Name an Italian football club", "Football clubs in Italy", "Juventus"),
    ("pt", "Name a Portuguese football club", "Football clubs in Portugal", "Benfica"),
    ("sco", "Name a Scottish football club", "Football clubs in Scotland", "Celtic"),
    ("wal", "Name a Welsh football club", "Football clubs in Wales", "Cardiff"),
    ("nl", "Name a Dutch football club", "Football clubs in the Netherlands", "Ajax"),
    ("hu", "Name a Hungarian football club", "Football clubs in Hungary", "Ferencvaros"),
    ("pe", "Name a Peruvian football club", "Football clubs in Peru", "Alianza"),
    ("th", "Name a Thai football club", "Football clubs in Thailand", "Buriram"),
    ("il", "Name an Israeli football club", "Football clubs in Israel", "Maccabi"),
    ("ru", "Name a Russian football club", "Football clubs in Russia", "Zenit"),
    ("fi", "Name a Finnish football club", "Football clubs in Finland", "HJK"),
    ("cn", "Name a Chinese football club", "Football clubs in China", "Shanghai"),
    ("sk", "Name a Slovak football club", "Football clubs in Slovakia", "Slovan"),
    ("tr", "Name a Turkish football club", "Football clubs in Turkey", "Galatasaray"),
    ("fr", "Name a French football club", "Football clubs in France", "Marseille"),
    ("rs", "Name a Serbian football club", "Football clubs in Serbia", "Red Star"),
    ("efl", "Name an English Football League club", "English Football League clubs", "Leeds"),
    ("br", "Name a Brazilian football club", "Football clubs in Brazil", "Flamengo"),
    ("ar", "Name an Argentine football club", "Football clubs in Argentina", "Boca"),
    ("mx", "Name a Mexican football club", "Football clubs in Mexico", "America"),
    ("jp", "Name a Japanese football club", "Football clubs in Japan", "Urawa"),
    ("kr", "Name a South Korean football club", "Football clubs in South Korea", "Seoul"),
    ("au", "Name an Australian football club", "Football clubs in Australia", "Sydney"),
    ("be", "Name a Belgian football club", "Football clubs in Belgium", "Anderlecht"),
    ("at", "Name an Austrian football club", "Football clubs in Austria", "Salzburg"),
    ("se", "Name a Swedish football club", "Football clubs in Sweden", "Malmo"),
    ("dk", "Name a Danish football club", "Football clubs in Denmark", "Copenhagen"),
    ("pl", "Name a Polish football club", "Football clubs in Poland", "Legia"),
    ("gr", "Name a Greek football club", "Football clubs in Greece", "Olympiacos"),
    ("cz", "Name a Czech football club", "Football clubs in the Czech Republic", "Sparta"),
    ("ie", "Name an Irish football club", "Football clubs in the Republic of Ireland", "Shamrock"),
]

_RIVERS = [
    ("de", "Name a river in Germany", "Rivers of Germany", "Rhine"),
    ("ro", "Name a river in Romania", "Rivers of Romania", "Danube"),
    ("nz", "Name a river in New Zealand", "Rivers of New Zealand", "Waikato"),
    ("fr", "Name a river in France", "Rivers of France", "Seine"),
    ("it", "Name a river in Italy", "Rivers of Italy", "Tiber"),
    ("pl", "Name a river in Poland", "Rivers of Poland", "Vistula"),
    ("jp", "Name a river in Japan", "Rivers of Japan", "Shinano"),
    ("es", "Name a river in Spain", "Rivers of Spain", "Ebro"),
    ("us-mo", "Name a river in Missouri", "Rivers of Missouri", "Mississippi"),
    ("us-pa", "Name a river in Pennsylvania", "Rivers of Pennsylvania", "Susquehanna"),
    ("us-ny", "Name a river in New York", "Rivers of New York (state)", "Hudson"),
    ("us-nc", "Name a river in North Carolina", "Rivers of North Carolina", "Roanoke"),
    ("us-mn", "Name a river in Minnesota", "Rivers of Minnesota", "Mississippi"),
]

_MOUNTAINS = [
    ("ch", "Name a mountain in Switzerland", "Mountains of Switzerland", "Matterhorn"),
    ("kr", "Name a mountain in South Korea", "Mountains of South Korea", "Hallasan"),
    ("by", "Name a mountain in Bavaria", "Mountains of Bavaria", "Zugspitze"),
    ("wa", "Name a mountain in Washington state", "Mountains of Washington (state)", "Rainier"),
    ("ny", "Name a mountain in New York state", "Mountains of New York (state)", "Marcy"),
    ("it", "Name a mountain in Italy", "Mountains of Italy", "Etna"),
]

_LAKES = [
    ("mn", "Name a lake in Minnesota", "Lakes of Minnesota", "Minnetonka"),
    ("ny", "Name a lake in New York state", "Lakes of New York (state)", "Champlain"),
    ("ch", "Name a lake in Switzerland", "Lakes of Switzerland", "Geneva"),
    ("mi", "Name a lake in Michigan", "Lakes of Michigan", "Huron"),
    ("fl", "Name a lake in Florida", "Lakes of Florida", "Okeechobee"),
    ("wi", "Name a lake in Wisconsin", "Lakes of Wisconsin", "Winnebago"),
]

_ISLANDS = [
    ("ak", "Name an island in Alaska", "Islands of Alaska", "Kodiak"),
    ("mv", "Name an island in the Maldives", "Islands of the Maldives", "Male"),
    ("in", "Name an island of India", "Islands of India", "Andaman"),
]

_CASTLES = [
    ("ir", "Name a castle in Iran", "Castles in Iran", "Alamut"),
    ("be", "Name a castle in Belgium", "Castles in Belgium", "Gravensteen"),
    ("it", "Name a castle in Italy", "Castles in Italy", "Angelo"),
    ("pt", "Name a castle in Portugal", "Castles in Portugal", "Pena"),
    ("fr", "Name a castle in France", "Castles in France", "Chambord"),
    ("es", "Name a castle in Spain", "Castles in Spain", "Alhambra"),
    ("en", "Name a castle in England", "Castles in England", "Windsor"),
    ("pl", "Name a castle in Poland", "Castles in Poland", "Malbork"),
    ("at", "Name a castle in Austria", "Castles in Austria", "Hohensalzburg"),
]

_VOLCANOES = [
    ("active", "Name an active volcano", "Active volcanoes", "Kilauea"),
]

# (suffix, text, topic, category, must) — incoming-link search.
_LINKED = [
    ("actor-us-m", "Name an American actor", "culture", "American male film actors", "Tom Hanks"),
    ("actor-us-f", "Name an American actress", "culture", "American film actresses", "Meryl"),
    ("actor-uk-m", "Name a British actor", "culture", "English male film actors", "Olivier"),
    ("writer-us", "Name an American screenwriter", "culture", "American male screenwriters", "Sorkin"),
    ("dir-fr", "Name a French film director", "culture", "French film directors", "Truffaut"),
    ("dir-it", "Name an Italian film director", "culture", "Italian film directors", "Fellini"),
    ("dir-jp", "Name a Japanese film director", "culture", "Japanese film directors", "Kurosawa"),
    ("dir-uk", "Name a film director from London", "culture", "Film directors from London", "Hitchcock"),
    ("dir-in", "Name an Indian film director", "culture", ["Indian film directors", "Bengali film directors"], "Satyajit"),
    ("bball", "Name an American basketball player", "sport", "American men's basketball players", "Michael Jordan"),
    ("cricket-in", "Name an Indian cricketer", "sport", "Indian cricketers", "Tendulkar"),
    ("cricket-au", "Name an Australian cricketer", "sport", "Australian cricketers", "Bradman"),
    ("cricket-en", "Name an English cricketer", "sport", "English cricketers", "Botham"),
    ("cricket-pk", "Name a Pakistani cricketer", "sport", "Pakistani cricketers", "Imran"),
    ("cricket-za", "Name a South African cricketer", "sport", "South African cricketers", "Kallis"),
    ("pitcher", "Name a Major League pitcher", "sport", "Major League Baseball pitchers", "Koufax"),
    ("qb", "Name an NFL quarterback", "sport", "American football quarterbacks", "Brady"),
    ("tennis-us", "Name an American tennis player", "sport", "American male tennis players", "Agassi"),
    ("golf-us", "Name an American golfer", "sport", "American male golfers", "Nicklaus"),
    ("boxer-us", "Name an American boxer", "sport", "American male boxers", "Muhammad Ali"),
    ("rock-us", "Name an American rock musician", "music", "American rock musicians", "Springsteen"),
    ("rapper", "Name an American rapper", "music", "American rappers", "Tupac"),
    ("jazz", "Name a jazz musician", "music", "American jazz musicians", "Armstrong"),
    ("country", "Name an American country singer", "music", "American country singers", "Cash"),
    ("inventor", "Name an American inventor", "science", "American inventors", "Edison"),
    ("painter-nl", "Name a Dutch Golden Age painter", "culture", "Dutch Golden Age painters", "Rembrandt"),
    ("novel-us", "Name an American novelist", "culture", "20th-century American novelists", "Hemingway"),
    ("comic", "Name an American stand-up comedian", "culture", "American stand-up comedians", "Pryor"),
    ("astronaut", "Name an American astronaut", "science", "American astronauts", "Armstrong"),
    ("chef", "Name an American chef", "food", "American chefs", "Lagasse"),
    ("fashion", "Name an American fashion designer", "culture", "American fashion designers", "Klein"),
    ("architect", "Name an American architect", "culture", "American architects", "Lloyd Wright"),
    ("physicist", "Name an American physicist", "science", "American physicists", "Feynman"),
    ("explorer", "Name an explorer of North America", "history", "Explorers of North America", "Columbus"),
    ("pope", "Name a pope", "history", "Popes", "John Paul"),
    ("god-greek", "Name a Greek god", "culture", "Greek gods", "Zeus"),
    ("god-egypt", "Name an Egyptian god", "culture", "Egyptian gods", "Anubis"),
    ("lang-in", "Name a language of India", "language", "Languages of India", "Hindi"),
    ("currency", "Name a circulating currency", "everyday", "Circulating currencies", "Euro"),
    ("genre-lit", "Name a literary genre", "culture", "Literary genres", "Mystery"),
    ("genre-music", "Name a musical genre", "music", "Music genres", "Reggae"),
    ("art-move", "Name an art movement", "culture", "Art movements", "Cubism"),
    ("arch-style", "Name an architectural style", "culture", "Architectural styles", "Gothic"),
    ("speech", "Name a figure of speech", "language", "Figures of speech", "Metaphor"),
    ("anthem", "Name a national anthem", "culture", "National anthems", "Marseillaise"),
    ("star", "Name a star", "science", "Stars with proper names", "Sirius"),
    ("dino", "Name a dinosaur", "nature", "Dinosaur genera", "Tyrannosaurus"),
    ("bird", "Name a bird", "nature", ["Birds of Europe", "Birds of North America", "Birds of the United States"], "Eagle"),
    ("messier", "Name a Messier object", "science", "Messier objects", "Andromeda"),
    ("igneous", "Name an igneous rock", "science", "Igneous rocks", "Granite"),
    ("sediment", "Name a sedimentary rock", "science", "Sedimentary rocks", "Sandstone"),
    ("antibiotic", "Name an antibiotic", "science", "Antibiotics", "Penicillin"),
    ("enzyme", "Name an enzyme", "science", "Enzymes", "Amylase"),
    ("mineral", "Name a mineral", "science", "Minerals", "Quartz"),
    ("crypto", "Name a cryptocurrency", "culture", "Cryptocurrencies", "Bitcoin"),
    ("alkaloid", "Name an alkaloid", "science", "Alkaloids", "Caffeine"),
    ("film-genre", "Name a film genre", "culture", "Film genres", "Western"),
    ("tv-genre", "Name a television genre", "culture", "Television genres", "Sitcom"),
    ("game-genre", "Name a video game genre", "game", "Video game genres", "Puzzle"),
    ("film-comedy-us", "Name an American comedy film", "film", "American comedy films", "Groundhog"),
    ("film-comedy-uk", "Name a British comedy film", "film", "British comedy films", "Monty"),
    ("film-horror", "Name an American horror film", "film", "American horror films", "Halloween"),
    ("anime", "Name an anime series", "culture", "Anime series", "Naruto"),
    ("manga", "Name a manga series", "culture", "Manga series", "Naruto"),
    ("broadway", "Name a Broadway musical", "culture", "Broadway musicals", "Hamilton"),
    ("fighting", "Name a fighting game", "game", "Fighting games", "Street Fighter"),
    ("fps", "Name a first-person shooter", "game", "First-person shooters", "Halo"),
    ("rpg", "Name a role-playing game", "game", "Role-playing video games", "Final Fantasy"),
    ("sim", "Name a simulation game", "game", "Simulation video games", "SimCity"),
    ("franchise-game", "Name a video game franchise", "game", "Video game franchises", "Zelda"),
    ("franchise", "Name a media franchise", "culture", "Media franchises", "Star Wars"),
    ("ps4", "Name a PlayStation 4 game", "game", "PlayStation 4 games", "Last of Us"),
    ("ios", "Name an iOS game", "game", "IOS games", "Angry Birds"),
    ("windows", "Name a Windows game", "game", "Windows games", "Minecraft"),
    ("marvel", "Name a Marvel superhero", "culture", "Marvel Comics superheroes", "Spider-Man"),
    ("dc", "Name a DC superhero", "culture", "DC Comics superheroes", "Batman"),
    ("disney-char", "Name a Disney comics character", "culture", "Disney comics characters", "Donald"),
    ("nintendo-fr", "Name a Nintendo franchise", "game", "Nintendo franchises", "Mario"),
    ("heritage-it", "Name a World Heritage Site in Italy", "geography", "World Heritage Sites in Italy", "Pompeii"),
    ("statepark-ca", "Name a state park in California", "geography", "State parks of California", "Malibu"),
    ("hat", "Name a kind of hat", "everyday", "Hats", "Beret"),
    ("furniture", "Name a piece of furniture", "everyday", "Furniture", "Sofa"),
    ("house", "Name a kind of house", "everyday", "House types", "Bungalow"),
    ("herb", "Name a culinary herb", "food", "Herbs", "Basil"),
    ("berry", "Name a berry", "food", "Berries", "Strawberry"),
    ("apple", "Name a kind of apple", "food", "Apple cultivars", "Granny Smith"),
    ("sauce", "Name a sauce", "food", "Sauces", "Ketchup"),
    ("salad", "Name a salad", "food", "Salads", "Caesar"),
    ("fast-dish", "Name a fast food dish", "food", "Fast food", "burger"),
    ("bread", "Name a kind of bread", "food", "Breads", "Baguette"),
    ("cake", "Name a kind of cake", "food", "Cakes", "Cheesecake"),
    ("icecream", "Name an ice cream brand", "food", "Ice cream brands", "Dazs"),
    ("dish", "Name a national dish", "food", "National dishes", "Paella"),
    ("street", "Name a street food", "food", "Street food", "Kebab"),
    ("rice", "Name a rice dish", "food", "Rice dishes", "Risotto"),
    ("dumpling", "Name a dumpling", "food", "Dumplings", "Pierogi"),
    ("mushroom", "Name an edible mushroom", "food", "Edible fungi", "Shiitake"),
    ("actor-in", "Name an Indian actor", "culture", "Indian male film actors", "Amitabh"),
    ("actor-fr", "Name a French actor", "culture", "French male film actors", "Belmondo"),
    ("actor-de", "Name a German actor", "culture", "German male film actors", "Waltz"),
    ("actor-it", "Name an Italian actor", "culture", "Italian male film actors", "Mastroianni"),
    ("actor-kr", "Name a South Korean actor", "culture", "South Korean male film actors", "Kang"),
    ("actor-jp", "Name a Japanese actor", "culture", "Japanese male film actors", "Mifune"),
    ("actor-es", "Name a Spanish actor", "culture", "Spanish male film actors", "Banderas"),
    ("actor-uk-f", "Name a British actress", "culture", "English film actresses", "Dench"),
    ("singer-us", "Name an American singer", "music", "American male singers", "Sinatra"),
    ("singer-uk", "Name a British singer", "music", "English male singers", "Bowie"),
    ("soul", "Name an American soul musician", "music", "American soul musicians", "Aretha"),
    ("britpop", "Name a Britpop band", "music", "Britpop groups", "Oasis"),
    ("kpop-singer", "Name a K-pop singer", "music", "K-pop singers", "BoA"),
    ("novel-uk", "Name a British novelist", "culture", "20th-century British novelists", "Orwell"),
    ("poet-us", "Name an American poet", "culture", "20th-century American poets", "Frost"),
    ("poet-uk", "Name a British poet", "culture", "British poets", "Keats"),
    ("playwright", "Name an American playwright", "culture", "American dramatists and playwrights", "Albee"),
    ("painter-us", "Name an American painter", "culture", "American painters", "Hopper"),
    ("photo", "Name an American photographer", "culture", "American photographers", "Leibovitz"),
    ("comic-strip", "Name an American comic strip", "culture", "American comic strips", "Peanuts"),
    ("film-drama", "Name an American drama film", "film", "American drama films", "Godfather"),
    ("film-crime", "Name an American crime film", "film", "American crime films", "Goodfellas"),
    ("film-action", "Name an American action film", "film", "American action films", "Terminator"),
    ("film-drama-uk", "Name a British drama film", "film", "British drama films", "Lawrence"),
    ("studio", "Name a video game company", "game", "Video game development companies", "Nintendo"),
    ("grammy", "Name a Grammy winner", "music", "Grammy Award winners", "Beyonc"),
    ("nobel-chem", "Name a Nobel chemistry laureate", "science", "Nobel laureates in Chemistry", "Curie"),
    ("nobel-med", "Name a Nobel medicine laureate", "science", "Nobel laureates in Physiology or Medicine", "Fleming"),
    ("nobel-peace", "Name a Nobel Peace Prize laureate", "history", "Nobel Peace Prize laureates", "Mandela"),
    ("disease", "Name an infectious disease", "science", "Infectious diseases", "Malaria"),
    ("vaccine", "Name a vaccine", "science", "Vaccines", "Polio"),
    ("fish", "Name a food fish", "food", "Commercial fish", "Salmon"),
    ("fruit-trop", "Name a tropical fruit", "food", "Tropical fruit", "Mango"),
    ("flatbread", "Name a flatbread", "food", "Flatbreads", "Naan"),
    ("coffee-brand", "Name a coffee brand", "food", "Coffee brands", "Starbucks"),
    ("beer-brand", "Name a beer brand", "food", "Beer brands", "Guinness"),
    ("cattle", "Name a cattle breed", "nature", "Cattle breeds", "Angus"),
    ("chicken", "Name a chicken breed", "nature", "Chicken breeds", "Leghorn"),
    ("sheep", "Name a sheep breed", "nature", "Sheep breeds", "Merino"),
    ("pig", "Name a pig breed", "nature", "Pig breeds", "Yorkshire"),
    ("toyota", "Name a Toyota vehicle", "culture", "Toyota vehicles", "Corolla"),
    ("ford", "Name a Ford vehicle", "culture", "Ford vehicles", "Mustang"),
    ("ferrari", "Name a Ferrari", "culture", "Ferrari vehicles", "Testarossa"),
    ("la-hood", "Name a Los Angeles neighborhood", "geography", "Neighborhoods in Los Angeles", "Hollywood"),
    ("park-ny", "Name a state park in New York", "geography", "State parks of New York (state)", "Letchworth"),
    ("park-fl", "Name a state park in Florida", "geography", "State parks of Florida", "Bahia"),
    ("park-tx", "Name a state park in Texas", "geography", "State parks of Texas", "Palo Duro"),
    ("heritage-fr", "Name a World Heritage Site in France", "geography", "World Heritage Sites in France", "Versailles"),
    ("heritage-cn", "Name a World Heritage Site in China", "geography", "World Heritage Sites in China", "Forbidden"),
    ("heritage-in", "Name a World Heritage Site in India", "geography", "World Heritage Sites in India", "Taj"),
    ("heritage-es", "Name a World Heritage Site in Spain", "geography", "World Heritage Sites in Spain", "Alhambra"),
    ("kami", "Name a Shinto kami", "culture", "Shinto kami", "Amaterasu"),
    ("god-roman", "Name a Roman god", "culture", "Roman gods", "Jupiter"),
    ("social", "Name a social network", "culture", "Social networking services", "Facebook"),
    ("circuit", "Name a Formula One circuit", "sport", "Formula One circuits", "Monaco"),
    ("eagle", "Name an eagle", "nature", "Eagles", "Bald"),
    ("duck", "Name a duck", "nature", "Ducks", "Mallard"),
    ("fabric", "Name a fabric", "everyday", "Woven fabrics", "Denim"),
    ("card", "Name a playing card game", "culture", "Card games", "Poker"),
    ("dog", "Name a dog breed", "nature", "Dog breeds", "Beagle"),
    ("cat", "Name a cat breed", "nature", "Cat breeds", "Siamese"),
    ("horse", "Name a horse breed", "nature", "Horse breeds", "Arabian"),
    ("cheese", "Name a cheese", "food", "Cheeses", "Cheddar"),
    ("pasta", "Name a pasta shape", "food", "Types of pasta", "Spaghetti"),
]


_CITY_BAN = ["list of", "metropolitan", "census"]
_CLUB_BAN = ["list of", "supporters", "season"]


def general_jobs() -> list[dict]:
    from pipeline.jobs import _job

    jobs: list[dict] = []

    def add(suffix, text, topic, categories, must, **extra):
        if isinstance(categories, str):
            categories = [categories]
        if isinstance(must, str):
            must = [must]
        extra.setdefault("min_answers", 80)
        extra.setdefault("cap", ANSWER_CAP)
        ban = list(extra.pop("ban", ["list of"]))
        jobs.append(
            _job(
                f"wd-gk-{suffix}",
                text,
                topic,
                "gk",
                list(categories),
                must=list(must),
                ban=ban,
                **extra,
            )
        )

    for code, text, category, must in _US_CITIES:
        add(
            f"city-{code}",
            text,
            "geography",
            category,
            must,
            ban=_CITY_BAN,
            places_from_subcats=True,
            subcat_below=40,
        )
    for code, text, category, must in _REGION_CITIES:
        add(f"city-{code}", text, "geography", category, must, ban=_CITY_BAN)
    for code, text, category, must in _COUNTRY_CITIES:
        add(
            f"city-{code}",
            text,
            "geography",
            category,
            must,
            ban=_CITY_BAN,
            by_links=True,
            cap=LINK_CAP,
        )
    for code, text, category, must in _CLUBS:
        add(
            f"club-{code}",
            text,
            "sport",
            category,
            must,
            ban=_CLUB_BAN,
            follow_subcats=False,
        )
    for code, text, category, must in _RIVERS + _MOUNTAINS + _LAKES + _ISLANDS + _CASTLES + _VOLCANOES:
        kind = "river"
        if code and text.startswith("Name a mountain"):
            kind = "mtn"
        elif text.startswith("Name a lake"):
            kind = "lake"
        elif text.startswith("Name an island") or text.startswith("Name a Philippine"):
            kind = "isle"
        elif text.startswith("Name a castle"):
            kind = "castle"
        elif "volcano" in text:
            kind = "volc"
        elif text.startswith("Name a river"):
            kind = "river"
        add(f"{kind}-{code}", text, "geography", category, must, ban=["list of"], follow_subcats=False)

    binomial = {"bird", "mushroom", "fish", "fruit-trop", "eagle", "duck"}
    for suffix, text, topic, category, must in _LINKED:
        extra = {"by_links": True, "cap": LINK_CAP}
        if suffix in binomial or suffix == "mushroom":
            extra["drop_binomial"] = True
        # Dog/cat/horse/cheese/pasta already exist as curated or specials.
        # Keep them out so the bank does not ask the same question twice.
        if suffix in {"dog", "cat", "horse", "cheese", "pasta", "card"}:
            continue
        add(suffix, text, topic, category, must, **extra)

    ids = [job["id"] for job in jobs]
    texts = [job["text"] for job in jobs]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate general-knowledge id")
    if len(texts) != len(set(texts)):
        raise RuntimeError("duplicate general-knowledge prompt")
    return jobs
