"""Easy American prompts. Lines are most-familiar first. Aliases follow a pipe."""

US = [
    {
        "id": "cur-nfl",
        "text": "Name an NFL team",
        "category": "sport",
        "gem": "Jacksonville Jaguars",
        "answers": """
Dallas Cowboys|Cowboys
New England Patriots|Patriots
Kansas City Chiefs|Chiefs
Green Bay Packers|Packers
San Francisco 49ers|49ers|Niners
Pittsburgh Steelers|Steelers
Philadelphia Eagles|Eagles
New York Giants|Giants
Chicago Bears|Bears
Miami Dolphins|Dolphins
Las Vegas Raiders|Raiders|Oakland Raiders
Denver Broncos|Broncos
Seattle Seahawks|Seahawks
Baltimore Ravens|Ravens
Buffalo Bills|Bills
Minnesota Vikings|Vikings
New Orleans Saints|Saints
Tampa Bay Buccaneers|Buccaneers|Bucs
Cleveland Browns|Browns
Cincinnati Bengals|Bengals
Indianapolis Colts|Colts
Tennessee Titans|Titans
Houston Texans|Texans
Los Angeles Chargers|Chargers|San Diego Chargers
Los Angeles Rams|Rams
Arizona Cardinals|Cardinals
Detroit Lions|Lions
Atlanta Falcons|Falcons
Carolina Panthers|Panthers
New York Jets|Jets
Washington Commanders|Commanders
Jacksonville Jaguars|Jaguars
""",
    },
    {
        "id": "cur-nba",
        "text": "Name an NBA team",
        "category": "sport",
        "gem": "Charlotte Hornets",
        "answers": """
Los Angeles Lakers|Lakers
Boston Celtics|Celtics
Chicago Bulls|Bulls
Golden State Warriors|Warriors
Miami Heat|Heat
New York Knicks|Knicks
San Antonio Spurs|Spurs
Dallas Mavericks|Mavericks|Mavs
Philadelphia 76ers|Sixers|76ers
Houston Rockets|Rockets
Brooklyn Nets|Nets
Los Angeles Clippers|Clippers
Milwaukee Bucks|Bucks
Phoenix Suns|Suns
Denver Nuggets|Nuggets
Oklahoma City Thunder|Thunder
Portland Trail Blazers|Trail Blazers|Blazers
Utah Jazz|Jazz
Minnesota Timberwolves|Timberwolves|Wolves
Toronto Raptors|Raptors
Atlanta Hawks|Hawks
Orlando Magic|Magic
Washington Wizards|Wizards
Indiana Pacers|Pacers
Detroit Pistons|Pistons
Cleveland Cavaliers|Cavaliers|Cavs
Memphis Grizzlies|Grizzlies
New Orleans Pelicans|Pelicans
Sacramento Kings|Kings
Charlotte Hornets|Hornets
""",
    },
    {
        "id": "cur-mlb",
        "text": "Name an MLB team",
        "category": "sport",
        "gem": "Tampa Bay Rays",
        "answers": """
New York Yankees|Yankees
Los Angeles Dodgers|Dodgers
Boston Red Sox|Red Sox
Chicago Cubs|Cubs
San Francisco Giants|Giants
St. Louis Cardinals|Cardinals
Atlanta Braves|Braves
Chicago White Sox|White Sox
Detroit Tigers|Tigers
Houston Astros|Astros
New York Mets|Mets
Philadelphia Phillies|Phillies
Cincinnati Reds|Reds
Baltimore Orioles|Orioles
Cleveland Guardians|Guardians|Cleveland Indians
Los Angeles Angels|Angels|Anaheim Angels
Seattle Mariners|Mariners
Texas Rangers|Rangers
Minnesota Twins|Twins
Milwaukee Brewers|Brewers
Pittsburgh Pirates|Pirates
Kansas City Royals|Royals
San Diego Padres|Padres
Washington Nationals|Nationals
Colorado Rockies|Rockies
Arizona Diamondbacks|Diamondbacks|D-backs
Miami Marlins|Marlins
Toronto Blue Jays|Blue Jays
Athletics|Oakland Athletics|A's
Tampa Bay Rays|Rays
""",
    },
    {
        "id": "cur-capital",
        "text": "Name a US state capital",
        "category": "geography",
        "gem": "Montpelier",
        "answers": """
Boston
Atlanta
Denver
Austin
Phoenix
Honolulu
Nashville
Sacramento
Columbus
Indianapolis
Salt Lake City
Oklahoma City
Santa Fe
Richmond
Raleigh
Madison
Saint Paul|St. Paul
Des Moines
Boise
Juneau
Albany
Hartford
Providence
Concord
Augusta
Trenton
Harrisburg
Annapolis
Dover
Columbia
Tallahassee
Montgomery
Jackson
Frankfort
Lansing
Springfield
Lincoln
Topeka
Jefferson City
Little Rock
Baton Rouge
Carson City
Salem
Olympia
Charleston
Cheyenne
Helena
Pierre
Bismarck
Montpelier
""",
    },
    {
        "id": "cur-city-ca",
        "text": "Name a city in California",
        "category": "geography",
        "gem": "Barstow",
        "answers": """
Los Angeles|LA|L.A.
San Francisco|SF|San Fran
San Diego
San Jose
Sacramento
Oakland
Fresno
Long Beach
Bakersfield
Anaheim
Santa Ana
Riverside
Irvine
Santa Monica
Pasadena
Berkeley
Beverly Hills
Palo Alto
Santa Barbara
San Luis Obispo
Santa Cruz
Monterey
Napa
Palm Springs
Malibu
Newport Beach
Laguna Beach
Santa Rosa
Redding
San Bernardino
Modesto
Oceanside
Carlsbad
Ventura
Salinas
Stockton
Fremont
Eureka
Visalia
Barstow
""",
    },
    {
        "id": "cur-tv",
        "text": "Name a TV show",
        "category": "culture",
        "gem": "Columbo",
        "answers": """
Friends
The Office
Seinfeld
The Simpsons
Family Guy
South Park
Game of Thrones
Breaking Bad
The Sopranos
Stranger Things
Grey's Anatomy
The Big Bang Theory
How I Met Your Mother
Modern Family
Parks and Recreation
The Walking Dead
Lost
Survivor
The Bachelor
American Idol
Saturday Night Live|SNL
Law & Order
NCIS
CSI
House
Cheers
The Twilight Zone
The X-Files
Gilmore Girls
The Fresh Prince of Bel-Air|Fresh Prince
Full House
SpongeBob SquarePants|SpongeBob
Rick and Morty
Ted Lasso
The Mandalorian
The Good Place
Arrested Development
Succession
The Wire
Mad Men
This Is Us
Yellowstone
Wednesday
The Crown
Squid Game
Brooklyn Nine-Nine
Abbott Elementary
Schitt's Creek
Ozark
Columbo
""",
    },
    {
        "id": "cur-cereal",
        "text": "Name a breakfast cereal",
        "category": "food",
        "gem": "Grape-Nuts",
        "answers": """
Cheerios
Frosted Flakes
Lucky Charms
Froot Loops
Cinnamon Toast Crunch
Cocoa Puffs
Honey Nut Cheerios
Raisin Bran
Corn Flakes
Rice Krispies
Cap'n Crunch|Capn Crunch
Trix
Apple Jacks
Special K
Wheaties
Life
Chex
Honey Bunches of Oats
Frosted Mini-Wheats|Mini Wheats
Reese's Puffs
Cookie Crisp
Golden Grahams
Kix
Corn Pops
Fruity Pebbles
Cocoa Pebbles
Count Chocula
Honey Smacks
Shredded Wheat
Cocoa Krispies
Alpha-Bits
French Toast Crunch
Cinnamon Life
Multi Grain Cheerios
Grape-Nuts
""",
    },
    {
        "id": "cur-snack",
        "text": "Name a snack brand",
        "category": "food",
        "gem": "Pirate's Booty",
        "answers": """
Doritos
Cheetos
Lay's|Lays
Ruffles
Pringles
Fritos
Tostitos
Cheez-It|Cheez Its
Goldfish
Ritz
Oreo
Chips Ahoy
Pop-Tarts|Pop Tarts
Chex Mix
Takis
Funyuns
Combos
SunChips
Wheat Thins
Triscuits
Fig Newtons
Nilla Wafers
Teddy Grahams
Slim Jim
Planters
Corn Nuts
Cracker Jack
Nature Valley
Rice Krispies Treats
SkinnyPop
Smartfood
Bugles
Gardetto's|Gardettos
Kettle Brand
Pirate's Booty
""",
    },
    {
        "id": "cur-clothes-brand",
        "text": "Name a clothing brand",
        "category": "culture",
        "gem": "Lands' End",
        "answers": """
Nike
Adidas
Puma
Reebok
New Balance
Converse
Vans
Gap
Old Navy
Levi's|Levis
Wrangler
H&M
Zara
Uniqlo
Champion
Under Armour
Lululemon
Patagonia
The North Face|North Face
Columbia
Ralph Lauren
Tommy Hilfiger
Calvin Klein
American Eagle
Hollister
Abercrombie & Fitch|Abercrombie
Forever 21
Urban Outfitters
J.Crew|J Crew
Crocs
UGG|Uggs
Timberland
Skechers
Dr. Martens|Doc Martens
Carhartt
Dickies
L.L. Bean|LL Bean
Lands' End
""",
    },
    {
        "id": "cur-channel",
        "text": "Name a TV channel",
        "category": "culture",
        "gem": "C-SPAN",
        "answers": """
ABC
NBC
CBS
Fox
PBS
CNN
ESPN
HBO
MTV
Nickelodeon|Nick
Cartoon Network
Disney Channel
Food Network
HGTV
TLC
Bravo
AMC
FX
Comedy Central
Adult Swim
Syfy
TNT
TBS
USA Network|USA
History Channel|History
Discovery Channel|Discovery
Lifetime
Hallmark Channel|Hallmark
BET
VH1
MSNBC
Fox News
The Weather Channel|Weather Channel
Animal Planet
National Geographic|Nat Geo
BBC America
Freeform
Paramount Network
TCM
C-SPAN|CSPAN
""",
    },
    {
        "id": "cur-holiday",
        "text": "Name a holiday",
        "category": "culture",
        "gem": "Flag Day",
        "answers": """
Christmas
Halloween
Thanksgiving
New Year's Day|New Years
Independence Day|Fourth of July|July 4th
Easter
Valentine's Day|Valentines Day
Mother's Day|Mothers Day
Father's Day|Fathers Day
Memorial Day
Labor Day
Martin Luther King Jr. Day|MLK Day
Presidents Day
Juneteenth
Veterans Day
St. Patrick's Day|Saint Patricks Day
Mardi Gras
Cinco de Mayo
Earth Day
April Fools' Day|April Fools
Groundhog Day
Hanukkah
Kwanzaa
Passover
Chinese New Year
Diwali
Ramadan
Black Friday
Christmas Eve
New Year's Eve|New Years Eve
Columbus Day
Indigenous Peoples' Day
Election Day
Super Bowl Sunday
Flag Day
""",
    },
    {
        "id": "cur-starwars",
        "text": "Name a Star Wars character",
        "category": "film",
        "gem": "Admiral Ackbar",
        "answers": """
Luke Skywalker|Luke
Darth Vader|Vader
Princess Leia|Leia|Leia Organa
Han Solo|Han
Chewbacca|Chewie
Yoda
Obi-Wan Kenobi|Obi-Wan|Ben Kenobi
R2-D2|R2D2|R2
C-3PO|C3PO|Threepio
Palpatine|Emperor Palpatine|Darth Sidious
Anakin Skywalker|Anakin
Padme Amidala|Padme
Rey
Kylo Ren|Ben Solo
Finn
Poe Dameron|Poe
BB-8|BB8
Grogu|Baby Yoda
The Mandalorian|Mando|Din Djarin
Boba Fett
Lando Calrissian|Lando
Jabba the Hutt|Jabba
Darth Maul|Maul
Mace Windu
Qui-Gon Jinn|Qui-Gon
Ahsoka Tano|Ahsoka
General Grievous|Grievous
Count Dooku|Dooku
Jar Jar Binks|Jar Jar
Grand Moff Tarkin|Tarkin
Stormtrooper
Wedge Antilles
Mon Mothma
Cassian Andor
Jango Fett
Captain Phasma|Phasma
Supreme Leader Snoke|Snoke
Rose Tico
Admiral Ackbar|Ackbar
""",
    },
    {
        "id": "cur-potter",
        "text": "Name a Harry Potter character",
        "category": "film",
        "gem": "Horace Slughorn",
        "answers": """
Harry Potter|Harry
Hermione Granger|Hermione
Ron Weasley|Ron
Albus Dumbledore|Dumbledore
Severus Snape|Snape
Voldemort|Tom Riddle|Lord Voldemort
Draco Malfoy|Draco
Rubeus Hagrid|Hagrid
Minerva McGonagall|McGonagall
Sirius Black|Sirius
Remus Lupin|Lupin
Bellatrix Lestrange|Bellatrix
Ginny Weasley|Ginny
Neville Longbottom|Neville
Luna Lovegood|Luna
Fred Weasley
George Weasley
Molly Weasley
Arthur Weasley
Dobby
Hedwig
Alastor Moody|Mad-Eye Moody
Lucius Malfoy
Dolores Umbridge|Umbridge
Peter Pettigrew|Wormtail
James Potter
Lily Potter
Cho Chang
Cedric Diggory|Cedric
Viktor Krum
Fleur Delacour
Ollivander
Argus Filch|Filch
Moaning Myrtle
Nearly Headless Nick
Kreacher
Newt Scamander|Newt
Gilderoy Lockhart
Sybill Trelawney
Horace Slughorn|Slughorn
""",
    },
    {
        "id": "cur-pokemon",
        "text": "Name a Pokemon",
        "category": "game",
        "gem": "Farfetch'd",
        "answers": """
Pikachu
Charizard
Bulbasaur
Charmander
Squirtle
Eevee
Jigglypuff
Meowth
Psyduck
Snorlax
Mewtwo
Mew
Gengar
Dragonite
Blastoise
Venusaur
Gyarados
Magikarp
Raichu
Lucario
Greninja
Gardevoir
Umbreon
Espeon
Jolteon
Vaporeon
Flareon
Lapras
Ditto
Togepi
Mudkip
Torchic
Treecko
Piplup
Chimchar
Turtwig
Chikorita
Cyndaquil
Totodile
Articuno
Zapdos
Moltres
Lugia
Ho-Oh
Rayquaza
Garchomp
Sylveon
Mimikyu
Farfetch'd
""",
    },
    {
        "id": "cur-simpsons",
        "text": "Name a Simpsons character",
        "category": "culture",
        "gem": "Hans Moleman",
        "answers": """
Homer Simpson|Homer
Marge Simpson|Marge
Bart Simpson|Bart
Lisa Simpson|Lisa
Maggie Simpson|Maggie
Ned Flanders|Flanders
Mr. Burns|Montgomery Burns|Burns
Waylon Smithers|Smithers
Krusty the Clown|Krusty
Principal Skinner|Seymour Skinner
Groundskeeper Willie|Willie
Chief Wiggum|Wiggum
Ralph Wiggum|Ralph
Moe Szyslak|Moe
Barney Gumble|Barney
Milhouse Van Houten|Milhouse
Nelson Muntz|Nelson
Apu Nahasapeemapetilon|Apu
Grandpa Simpson|Abe Simpson
Patty Bouvier|Patty
Selma Bouvier|Selma
Itchy
Scratchy
Comic Book Guy
Dr. Hibbert
Dr. Nick
Reverend Lovejoy
Troy McClure
Sideshow Bob
Edna Krabappel|Mrs. Krabappel
Fat Tony
Kent Brockman
Lionel Hutz
Rainier Wolfcastle
Santa's Little Helper
Snowball II
Otto Mann|Otto
Agnes Skinner
Cletus Spuckler|Cletus
Hans Moleman
""",
    },
    {
        "id": "cur-disney-char",
        "text": "Name a Disney character",
        "category": "film",
        "gem": "Mushu",
        "answers": """
Mickey Mouse|Mickey
Minnie Mouse|Minnie
Donald Duck|Donald
Daisy Duck|Daisy
Goofy
Pluto
Elsa
Anna
Olaf
Simba
Mufasa
Timon
Pumbaa
Ariel
Belle
Beast
Jasmine
Aladdin
Genie
Mulan
Moana
Maui
Cinderella
Snow White
Rapunzel
Tiana
Pocahontas
Stitch
Woody
Buzz Lightyear|Buzz
Mike Wazowski|Mike
Sulley
Nemo
Dory
Maleficent
Ursula
Scar
Hades
Winnie the Pooh|Pooh
Tigger
Baymax
Jack Skellington
Mushu
""",
    },
    {
        "id": "cur-game-char",
        "text": "Name a video game character",
        "category": "game",
        "gem": "Samus Aran",
        "answers": """
Mario
Luigi
Princess Peach|Peach
Bowser
Yoshi
Donkey Kong|DK
Link
Zelda
Pikachu
Sonic the Hedgehog|Sonic
Tails
Knuckles
Pac-Man|Pacman
Lara Croft
Master Chief
Kratos
Solid Snake|Snake
Cloud Strife|Cloud
Sephiroth
Ryu
Chun-Li
Scorpion
Sub-Zero
Crash Bandicoot|Crash
Spyro
Mega Man
Kirby
Fox McCloud|Fox
Steve|Minecraft Steve
Creeper
Geralt of Rivia|Geralt
Arthur Morgan
CJ|Carl Johnson
Ellie
Nathan Drake
Gordon Freeman
Glados|GLaDOS
Doomguy|Doom Slayer
Isabelle
Samus Aran|Samus
""",
    },
    {
        "id": "cur-animated",
        "text": "Name an animated movie",
        "category": "film",
        "gem": "The Iron Giant",
        "answers": """
Toy Story
The Lion King
Finding Nemo
Shrek
Frozen
Moana
Encanto
Up
WALL-E
Inside Out
The Incredibles
Monsters, Inc.|Monsters Inc
Cars
Coco
Ratatouille
How to Train Your Dragon
Kung Fu Panda
Despicable Me
Minions
Zootopia
Tangled
Aladdin
The Little Mermaid
Beauty and the Beast
Snow White and the Seven Dwarfs
Cinderella
Bambi
Pinocchio
Spider-Man: Into the Spider-Verse|Into the Spider-Verse
The Lego Movie
Shrek 2
Frozen 2
Toy Story 2
Finding Dory
Inside Out 2
The Super Mario Bros. Movie|Super Mario Bros Movie
Puss in Boots
Madagascar
Ice Age
Spirited Away
My Neighbor Totoro|Totoro
Howl's Moving Castle
Princess Mononoke
Akira
Wallace & Gromit: The Curse of the Were-Rabbit|Wallace and Gromit|Wallace & Gromit
Chicken Run
The Nightmare Before Christmas
Coraline
Soul
Turning Red
Luca
The Iron Giant
""",
    },
    {
        "id": "cur-director",
        "text": "Name a movie director",
        "category": "film",
        "gem": "John Carpenter",
        "answers": """
Steven Spielberg|Spielberg
Martin Scorsese|Scorsese
Christopher Nolan|Nolan
Quentin Tarantino|Tarantino
James Cameron
George Lucas
Alfred Hitchcock|Hitchcock
Francis Ford Coppola|Coppola
Ridley Scott
Tim Burton
Spike Lee
Wes Anderson
Jordan Peele
Greta Gerwig
Clint Eastwood
Stanley Kubrick|Kubrick
Peter Jackson
Guillermo del Toro
Denis Villeneuve
Ryan Coogler
David Fincher
Sofia Coppola
Kathryn Bigelow
Taika Waititi
James Gunn
Sam Raimi
Michael Bay
Robert Zemeckis
M. Night Shyamalan|Shyamalan
John Hughes
Ron Howard
Mel Brooks
Wes Craven
Orson Welles
Billy Wilder
Hayao Miyazaki|Miyazaki
Jon Favreau
Patty Jenkins
Ava DuVernay
John Carpenter
""",
    },
]
