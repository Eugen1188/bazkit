import re


SHOPPING_CATEGORY_CHOICES = (
    ("produce", "Obst & Gemüse"),
    ("bakery", "Brot & Backwaren"),
    ("meat_fish", "Fleisch & Fisch"),
    ("dairy_eggs", "Milchprodukte & Eier"),
    ("frozen", "Tiefkühl"),
    ("pantry", "Vorrat & Gewürze"),
    ("drinks", "Getränke"),
    ("household", "Haushalt & Drogerie"),
    ("other", "Sonstiges"),
)

SHOPPING_CATEGORY_META = {
    key: {"label": label, "order": order}
    for order, (key, label) in enumerate(SHOPPING_CATEGORY_CHOICES, start=1)
}

BLS_GROUP_CATEGORY = {
    "B": "bakery",
    "C": "pantry",
    "D": "bakery",
    "E": "pantry",
    "F": "produce",
    "G": "produce",
    "H": "pantry",
    "K": "produce",
    "M": "dairy_eggs",
    "N": "drinks",
    "P": "drinks",
    "Q": "pantry",
    "R": "pantry",
    "S": "pantry",
    "T": "meat_fish",
    "U": "meat_fish",
    "V": "meat_fish",
    "W": "meat_fish",
}

FROZEN = re.compile(r"tiefkühl|tiefgekühlt|tiefgefroren|\btk\b|frozen", re.I)
BAKERY = re.compile(
    r"brot|brötchen|toast|baguette|backware|croissant|knäckebrot",
    re.I,
)
MEAT_FISH = re.compile(
    r"fleisch|rind|schwein|hähn|huhn|pute|truthahn|lamm|kalb|wild|hack|"
    r"wurst|schinken|speck|fisch|lachs|thunfisch|kabeljau|seelachs|garnele|"
    r"meeresfr|muschel|krabbe",
    re.I,
)
DAIRY_EGGS = re.compile(
    r"milch|käse|joghurt|quark|sahne|schmand|crème fraîche|creme fraiche|"
    r"butter|margarine|\bei\b|eier|eigelb|eiklar|molke",
    re.I,
)
SHELF_STABLE = re.compile(
    r"konserve|\bdose\b|getrocknet|eingelegt|essiggurke|gewürzgurke|pulver|mark\b|passierte|passata|"
    r"whey|proteinpulver|protein powder|eiweißpulver|eiweisspulver|"
    r"nudel|pasta|spaghetti|makkaroni|reis|mehl|stärke|zucker|salz|gewürz|"
    r"pfeffer|paprika.*pulver|senf|sternanis|star\s+anise|aniseeds?|spices?|öl|essig|sauce|soße|brühe|fond|bouillon|"
    r"müsli|hafer|couscous|bulgur|quinoa|hirse|buchweizen|amaranth|"
    r"nuss|mandel|cashew|pistaz|samen|saaten|kerne|algen|tahini|miso|sojasauce|"
    r"backzutat|backpulver|natron|hefe|gelatine|kakao|sirup|honig|hülsenfr",
    re.I,
)
PRODUCE = re.compile(
    r"obst|gemüse|frucht|apfel|banane|beere|zitr|limette|orange|mango|"
    r"birne|pflaume|feige|dattel|salat|tomat|kartoff|paprika|chili|"
    r"zwiebel|knoblauch|gurke|zucchini|kürbis|karotte|möhre|pastinak|"
    r"sellerie|pilz|kohl|spinat|mangold|mais|bohne|erbse|linse|avocado|"
    r"kräuter|basilikum|petersilie|schnittlauch|koriander|rosmarin|"
    r"thymian|dill|salbei|ingwer|artischock|spargel|radies|rettich",
    re.I,
)
DRINKS = re.compile(
    r"getränk|wasser|saft|limonade|cola|kaffee|tee|bier|wein",
    re.I,
)
HOUSEHOLD = re.compile(
    r"papier|reiniger|spül|waschmittel|seife|shampoo|zahnpasta|deo|"
    r"haushalt|drogerie|müllbeutel|folie",
    re.I,
)

# Kandidaten, bei denen Nutzer häufig bereits einen Vorrat besitzen. Das ist
# bewusst nur eine Standardempfehlung; die spätere Benutzerentscheidung bleibt
# ausschlaggebend.
COMMON_PANTRY = re.compile(
    r"^(?:speise)?salz$|pfeffer|paprikapulver|kreuzkümmel|kurkuma|zimt|"
    r"muskat|kardamom|safran|gewürznelke|senf|fenchelsamen|sternanis|star\s+anise|"
    r"oregano$|majoran$|(?:thymian|rosmarin|basilikum)\s+getrocknet$|"
    r"lorbeer|öl$|essig$|zucker$|mehl|stärke|backpulver|natron|"
    r"brühe$|fond$|bouillon|reis$|nudeln$|pasta$|couscous$|bulgur$|"
    r"quinoa$|haferflocken$|honig$|sojasauce$|fischsauce$|sambal|miso$",
    re.I,
)


def infer_product_taxonomy(
    name,
    canonical_name="",
    source_category="",
    source="",
    external_id="",
):
    searchable = " ".join(filter(None, (canonical_name, name, source_category)))
    canonical = str(canonical_name or name or "").strip()

    if FROZEN.search(searchable):
        category = "frozen"
    elif BAKERY.search(searchable):
        category = "bakery"
    elif MEAT_FISH.search(searchable):
        category = "meat_fish"
    elif DAIRY_EGGS.search(searchable):
        category = "dairy_eggs"
    elif SHELF_STABLE.search(searchable):
        category = "pantry"
    elif DRINKS.search(searchable):
        category = "drinks"
    elif PRODUCE.search(searchable):
        category = "produce"
    elif HOUSEHOLD.search(searchable):
        category = "household"
    elif source == "bls":
        category = BLS_GROUP_CATEGORY.get(
            str(external_id or "")[:1].upper(),
            "other",
        )
    else:
        category = "other"

    return category, bool(COMMON_PANTRY.search(canonical))
