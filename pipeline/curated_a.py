"""Hand-curated prompts, most familiar answer first. Aliases follow a pipe."""

A = [
    {
        "id": "cur-spice",
        "text": "Name a spice",
        "category": "food",
        "gem": "Aleppo pepper",
        "answers": """
salt
black pepper|pepper
garlic|garlic powder
cinnamon
paprika
cumin
oregano
chili powder|chilli powder|chile powder
basil
ginger
onion powder
nutmeg
thyme
rosemary
cayenne|cayenne pepper
parsley
bay leaf|bay leaves
turmeric
dill
cilantro|coriander leaves
sage
clove|cloves
vanilla
cardamom
allspice
mustard|mustard seed
fennel
tarragon
smoked paprika
white pepper
saffron
star anise
celery seed
marjoram
caraway
red pepper flakes|chili flakes
sumac
fenugreek
mace
annatto
coriander|coriander seed
juniper|juniper berries
file powder|file
ajwain
grains of paradise
Aleppo pepper|aleppo
long pepper
cubeb
mahlab
asafoetida|hing
nigella|kalonji
urfa biber
sansho
""",
    },
    {
        "id": "cur-pasta",
        "text": "Name a pasta shape",
        "category": "food",
        "gem": "trofie",
        "answers": """
spaghetti
macaroni
penne
fettuccine
lasagna|lasagne
linguine
ramen
rigatoni
angel hair|capellini
rotini
farfalle|bowtie pasta|bow tie
egg noodles
orzo
tortellini
ravioli
ziti
shells|conchiglie
udon
rice noodles
vermicelli
bucatini
fusilli
tagliatelle
gnocchi
cannelloni
manicotti
lo mein
soba
pappardelle
orecchiette
ditalini
mafaldine
radiatore
campanelle
casarecce
gemelli
cavatelli
agnolotti
bigoli
paccheri
strozzapreti
cavatappi
stelline
calamarata
lumache
fideos
trofie
anelli
mezzalune
busiate
fileja
""",
    },
    {
        "id": "cur-fruit",
        "text": "Name a fruit",
        "category": "food",
        "gem": "mangosteen",
        "answers": """
apple
banana
orange
strawberry
grape
watermelon
pineapple
mango
peach
pear
cherry
blueberry
raspberry
lemon
lime
kiwi|kiwifruit
cantaloupe
honeydew
plum
apricot
grapefruit
blackberry
pomegranate
coconut
avocado
cranberry
papaya
fig
date
tangerine|mandarin
passion fruit|passionfruit
guava
lychee
persimmon
starfruit|carambola
dragon fruit|pitaya
jackfruit
quince
currant
gooseberry
mulberry
kumquat
rambutan
durian
plantain
nectarine
boysenberry
yuzu
soursop
cherimoya
mangosteen
feijoa
ugli fruit
""",
    },
    {
        "id": "cur-vegetable",
        "text": "Name a vegetable",
        "category": "food",
        "gem": "romanesco",
        "answers": """
carrot
broccoli
potato
tomato
onion
corn
lettuce
spinach
cucumber
pepper|bell pepper
celery
cabbage
cauliflower
green bean
pea|peas
mushroom
zucchini
squash
eggplant|aubergine
asparagus
brussels sprout|brussels sprouts
radish
beet|beetroot
sweet potato
kale
artichoke
leek
okra
turnip
parsnip
bok choy|pak choi
arugula|rocket
swiss chard
collard greens
watercress
jicama
kohlrabi
rutabaga
endive
radicchio
daikon
celeriac
taro
yam
chayote
sunchoke|jerusalem artichoke
romanesco
salsify
cardoon
fiddlehead
bamboo shoot
""",
    },
    {
        "id": "cur-cheese",
        "text": "Name a cheese",
        "category": "food",
        "gem": "Époisses",
        "answers": """
cheddar
mozzarella
parmesan|parmigiano
swiss
american cheese
provolone
gouda
brie
feta
blue cheese|bleu cheese
ricotta
monterey jack
colby
pepper jack
gruyere|gruyère
goat cheese|chevre
camembert
muenster
havarti
gorgonzola
cottage cheese
cream cheese
manchego
pecorino
asiago
fontina
emmental
roquefort
stilton
burrata
halloumi
paneer
queso fresco
mascarpone
comte|comté
taleggio
raclette
jarlsberg
edam
limburger
wensleydale
Époisses|epoisses
vacherin
reblochon
morbier
cabrales
idiazabal
scamorza
robiola
langres
""",
    },
    {
        "id": "cur-breakfast",
        "text": "Name a breakfast food",
        "category": "food",
        "gem": "toad in the hole",
        "answers": """
eggs
bacon
toast
cereal
pancakes
oatmeal|porridge
waffle|waffles
sausage
bagel
yogurt
fruit
hash brown|hashbrown
french toast
croissant
muffin
doughnut|donut
granola
smoothie
omelette|omelet
scrambled eggs
breakfast burrito
biscuit
grits
english muffin
cinnamon roll
scone
danish
breakfast sandwich
fried eggs
poached eggs
huevos rancheros
shakshuka
congee
full english
avocado toast
chilaquiles
eggs benedict
biscuits and gravy
nasi lemak
scrapple
goetta
johnny cakes
kedgeree
menemen
toad in the hole
bubble and squeak
changua
""",
    },
    {
        "id": "cur-cocktail",
        "text": "Name a cocktail",
        "category": "food",
        "gem": "The Last Word",
        "answers": """
margarita
martini
mojito
old fashioned
cosmopolitan|cosmo
manhattan
daiquiri
negroni
whiskey sour
pina colada|piña colada
bloody mary
gin and tonic
mai tai
moscow mule
long island iced tea|long island
paloma
aperol spritz
mimosa
caipirinha
sidecar
french 75
tom collins
mint julep
white russian
espresso martini
dark and stormy
sazerac
boulevardier
aviation
paper plane
bees knees|bee's knees
corpse reviver
vesper
singapore sling
pisco sour
zombie
hurricane
tequila sunrise
kamikaze
lemon drop
amaretto sour
irish coffee
hot toddy
bellini
gibson
rob roy
rusty nail
white lady
clover club
The Last Word|last word
""",
    },
    {
        "id": "cur-candy",
        "text": "Name a candy",
        "category": "food",
        "gem": "Curly Wurly",
        "answers": """
chocolate
m&ms|m and ms
snickers
kit kat
reeses|reese's
skittles
starburst
twix
hersheys|hershey bar
gummy bears
lollipop
candy corn
twizzlers
sour patch kids
milky way
butterfinger
almond joy
three musketeers
payday
baby ruth
nerds
jelly beans
licorice
tootsie roll
jolly rancher
lifesavers
york peppermint patty
rolo
cadbury
ferrero rocher
kinder
haribo
warheads
airheads
laffy taffy
whoppers
crunch
mounds
bit-o-honey
abba-zaba
violet crumble
Curly Wurly|curly wurly
charleston chew
zero bar
mary janes
clark bar
""",
    },
    {
        "id": "cur-soda",
        "text": "Name a soft drink",
        "category": "food",
        "gem": "Irn-Bru",
        "answers": """
coke|coca-cola|coca cola
pepsi
sprite
dr pepper
fanta
mountain dew
7up|seven up
ginger ale
root beer
lemonade
orange soda
cola
sierra mist
crush
sunkist
barqs|barq's
canada dry
schweppes
la croix
perrier
san pellegrino
topo chico
jarritos
ramune
cream soda
birch beer
big red
cheerwine
moxie
vernors
faygo
shasta
rc cola|r.c. cola
fresca
squirt
mug root beer
ibc
boylan
mexican coke
fentimans
bundaberg
Irn-Bru|irn bru|irn-bru
nehi
tab
orangina
chinotto
sanbitter
kinnie
""",
    },
]
