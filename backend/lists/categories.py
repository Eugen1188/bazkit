import re


CATEGORY_RULES = (
    (
        "produce",
        "Obst & Gemüse",
        re.compile(
            r"obst|gemüse|frucht|apfel|banane|beere|zitr|salat|tomat|kartoff|"
            r"paprika|chili|zwiebel|knoblauch|gurke|zucchini|kürbis|karotte|möhre|"
            r"pilz|kohl|spinat|mais|bohne|erbse|linse|avocado|kräuter",
            re.I,
        ),
    ),
    (
        "bakery",
        "Brot & Backwaren",
        re.compile(r"brot|brötchen|toast|baguette|backware|kuchen|gebäck|croissant", re.I),
    ),
    (
        "meat_fish",
        "Fleisch & Fisch",
        re.compile(
            r"fleisch|rind|schwein|hähn|pute|lamm|hack|wurst|schinken|fisch|lachs|"
            r"thunfisch|garnele|meeresfr",
            re.I,
        ),
    ),
    (
        "dairy_eggs",
        "Milchprodukte & Eier",
        re.compile(
            r"milch|käse|joghurt|quark|sahne|butter|margarine|ei\b|eier|molke",
            re.I,
        ),
    ),
    (
        "frozen",
        "Tiefkühl",
        re.compile(r"tiefkühl|tiefgekühlt|gefroren|eiscreme|speiseeis", re.I),
    ),
    (
        "drinks",
        "Getränke",
        re.compile(r"getränk|wasser|saft|limonade|cola|kaffee|tee|bier|wein", re.I),
    ),
    (
        "pantry",
        "Vorrat & Gewürze",
        re.compile(
            r"nudel|pasta|spaghetti|makkaroni|reis|mehl|zucker|salz|gewürz|öl|essig|konserve|dose|"
            r"sauce|soße|brühe|müsli|hafer|couscous|bulgur|nuss|samen",
            re.I,
        ),
    ),
    (
        "household",
        "Haushalt & Drogerie",
        re.compile(
            r"papier|reiniger|spül|waschmittel|seife|shampoo|zahnpasta|deo|"
            r"haushalt|drogerie|müllbeutel|folie",
            re.I,
        ),
    ),
)

CATEGORY_ORDER = {
    "produce": 10,
    "bakery": 20,
    "meat_fish": 30,
    "dairy_eggs": 40,
    "frozen": 50,
    "pantry": 60,
    "drinks": 70,
    "household": 80,
    "other": 90,
}


def shopping_category(item):
    product = getattr(item, "product", None)
    searchable = " ".join(filter(None, [
        getattr(item, "name", ""),
        getattr(product, "name", ""),
        getattr(product, "canonical_name", ""),
        getattr(product, "category", ""),
    ]))
    for key, label, pattern in CATEGORY_RULES:
        if pattern.search(searchable):
            return key, label, CATEGORY_ORDER[key]
    return "other", "Sonstiges", CATEGORY_ORDER["other"]
