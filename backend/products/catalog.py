import re
from decimal import Decimal, InvalidOperation

from .ingredient_catalog import canonical_query, curated_canonical_name


AMOUNT_SUFFIX = re.compile(
    r"(?:\s*[,\-–|/]?\s*|\s*\(\s*)"
    r"(?:\d+\s*[x×]\s*)?\d+(?:[.,]\d+)?\s*"
    r"(?:mg|g|kg|ml|cl|dl|l|liter)\b"
    r"(?:\s*(?:packung|flasche|dose|beutel|glas))?\s*\)?\s*$",
    re.I,
)

CANONICAL_RULES = (
    (re.compile(r"^(?:chili|chilli)(?:schote|schoten|pepper|peppers)?\b", re.I), "Chilischote"),
    (re.compile(r"^tomaten?\b(?=.*(?:konserve|dose|gehackt|stückig))", re.I), "Dosentomaten"),
    (re.compile(r"^(?:passierte?\s+tomaten?|tomaten?\s+passiert|passata)\b", re.I), "Passierte Tomaten"),
    (re.compile(r"^tomaten?(?:mark|paste)|^tomatenmark\b", re.I), "Tomatenmark"),
    (re.compile(r"^tomatensaft\b", re.I), "Tomatensaft"),
    (re.compile(r"^(?:h-)?milch\b(?=.*(?:1[,.]5|fettarm))", re.I), "Fettarme Milch"),
    (re.compile(r"^(?:h-)?milch\b|^vollmilch\b", re.I), "Milch"),
    (re.compile(r"^buttermilch\b", re.I), "Buttermilch"),
    (re.compile(r"^kokos(?:nuss)?milch\b", re.I), "Kokosmilch"),
    (re.compile(r"^(?:hähnchen|huhn|hühner)brust", re.I), "Hähnchenbrust"),
    (re.compile(r"^putenbrust", re.I), "Putenbrust"),
    (re.compile(r"^(?:cherry)?tomaten?\b", re.I), "Tomate"),
    (re.compile(r"^(?:gemüse)?paprika\s+rot\b", re.I), "Paprika rot"),
    (re.compile(r"^(?:gemüse)?paprika\s+gelb\b", re.I), "Paprika gelb"),
    (re.compile(r"^(?:gemüse)?paprika\s+grün\b", re.I), "Paprika grün"),
    (re.compile(r"^(?:bleich|stangen|stauden)sellerie\b", re.I), "Staudensellerie"),
    (re.compile(r"^knollensellerie\b", re.I), "Knollensellerie"),
    (re.compile(r"^(?:zwiebeln?)\b", re.I), "Zwiebel"),
    (re.compile(r"^knoblauch\b", re.I), "Knoblauch"),
    (re.compile(r"^kartoffeln?\b", re.I), "Kartoffel"),
    (re.compile(r"^(?:karotten?|möhren?)\b", re.I), "Karotte"),
    (re.compile(r"^(?:salat)?gurken?\b", re.I), "Gurke"),
    (re.compile(r"^äpfel?\b|^apfel\b", re.I), "Apfel"),
    (re.compile(r"^bananen?\b", re.I), "Banane"),
    (re.compile(r"^erdbeeren?\b", re.I), "Erdbeere"),
    (re.compile(r"^himbeeren?\b", re.I), "Himbeere"),
    (re.compile(r"^(?:blaubeeren?|heidelbeeren?)\b", re.I), "Blaubeere"),
    (re.compile(r"^hühnerei\s+eigelb\b|^eigelb\b", re.I), "Eigelb"),
    (re.compile(r"^hühnerei\s+eiklar\b|^eiklar\b|^eiwei(?:ß|ss)\b", re.I), "Eiklar"),
    (re.compile(r"^(?:ei|eier|hühnerei)(?:\s+roh)?$", re.I), "Ei"),
    (re.compile(r"^olivenöl\b", re.I), "Olivenöl"),
    (re.compile(r"^rapsöl\b", re.I), "Rapsöl"),
    (re.compile(r"^sonnenblumenöl\b", re.I), "Sonnenblumenöl"),
    (re.compile(r"^(?:speise|tafel)?salz\b", re.I), "Salz"),
    (re.compile(r"^weizenmehl$", re.I), "Weizenmehl Type 405"),
    (re.compile(r"^dinkelmehl$", re.I), "Dinkelmehl Type 630"),
    (re.compile(r"^roggenmehl$", re.I), "Roggenmehl Type 1150"),
    (re.compile(r"^zucker\b", re.I), "Zucker"),
    (re.compile(r"^butter\b", re.I), "Butter"),
)

ALLOWED_INGREDIENT = re.compile(
    r"\b(?:brühe|fond|tomatenmark|senf|ketchup|mayonnaise|sojasauce|pesto|essig|"
    r"semmelbrösel|paniermehl|kaffee|kaffeepulver|tee|kakaopulver|backkakao|"
    r"wein|bier|rum|cognac|sherry|marsala|schokolade|honig|sirup|zucker)\b",
    re.I,
)
PREPARED_FOOD = re.compile(
    r"(?:suppe|eintopf|pfanne|auflauf|pizza|lasagne|burger|sandwich|wrap|"
    r"bami\s+goreng|nasi\s+goreng|gulasch|ragout|frikassee|roulade|currygericht|"
    r"chili\s+(?:con|sin)\s+carne|"
    r"tellergericht|fertiggericht|menü|mahlzeit|risotto|paella|fischstäbchen|"
    r"cordon\s+bleu|döner|gyros|hot\s+dog|hamburger|ravioli|tortellini|"
    r"schupfnudeln|frikadelle|speiseeis|eiscreme)\b",
    re.I,
)
PREPARED_VARIANT = re.compile(
    r"\b(?:gebraten|frittiert|paniert|verzehrfertig|küchenfertig|zubereitet|"
    r"servierfertig|aufgebrüht|gekocht|gegart|geschmort|überbacken)"
    r"(?:e|en|em|er|es)?\b",
    re.I,
)
NON_INGREDIENT = re.compile(
    r"\b(?:nahrungsergänzung|vitaminpräparat|mineralstoffpräparat|säuglingsnahrung|"
    r"sondennahrung|limonade|cola|energydrink|energy-drink|erfrischungsgetränk|"
    r"eistee|cocktail|torte|kuchen|muffin|keks|plätzchen|praline|schokoriegel|"
    r"müsliriegel|chips|cracker|gummibonbon|bonbon|dessert|pudding|"
    r"milchmischgetränk|trinkjoghurt|frühstückscerealien)\b",
    re.I,
)
OFF_MEAL_CATEGORY = re.compile(
    r"(?:^|[,; ])(?:meals?|pizzas?|sandwiches?|frozen-meals?|prepared-meals?)"
    r"(?:$|[,; ])",
    re.I,
)


def clean_product_name(value):
    name = re.sub(r"\s+", " ", str(value or "")).strip()
    return AMOUNT_SUFFIX.sub("", name).strip(" ,-–")[:150]


def canonical_search_query(value):
    query = re.sub(r"\s+", " ", str(value or "")).strip()
    mapped = canonical_query(query)
    if mapped != query:
        return mapped
    compact = re.sub(r"[\s\-_]", "", query.casefold())
    if re.fullmatch(
        r"(?:chili|chilli)(?:s|schot+t?e?n?)?|peperoni(?:schot+t?e?n?)?",
        compact,
    ):
        return "Chilischote"
    return query


def canonical_recipe_name(value, source="", external_id=""):
    name = clean_product_name(value)
    curated = curated_canonical_name(source, external_id)
    if curated:
        return curated
    for pattern, replacement in CANONICAL_RULES:
        if pattern.search(name):
            return replacement
    canonical = re.sub(r"\([^)]*\)", "", name).split(",", 1)[0]
    canonical = re.sub(
        r"\b(?:roh|frisch|tiefgefroren|pasteurisiert|geschält|ungeschält)\b",
        "",
        canonical,
        flags=re.I,
    )
    canonical = re.sub(r"\s+", " ", canonical).strip(" ,-–/")
    return (canonical or name)[:150]


def recipe_ingredient_status(name, category="", source="", external_id=""):
    cleaned_name = clean_product_name(name)
    searchable = f"{cleaned_name} {category or ''}"
    if not cleaned_name:
        return False, "Produktname fehlt"
    if PREPARED_FOOD.search(searchable):
        return False, "Fertiggericht oder zusammengesetzte Speise"
    if PREPARED_VARIANT.search(cleaned_name) and not ALLOWED_INGREDIENT.search(cleaned_name):
        return False, "Bereits zubereitete Produktvariante"
    if NON_INGREDIENT.search(searchable) and not ALLOWED_INGREDIENT.search(cleaned_name):
        return False, "Kein typisches Kochprodukt"
    if source == "bls" and str(external_id or "").upper().startswith(("X", "Y")):
        return False, "BLS-Rezeptur oder zusammengesetzte Speise"
    if source == "open_food_facts" and OFF_MEAL_CATEGORY.search(str(category or "")):
        return False, "Open-Food-Facts-Kategorie Fertiggericht"
    return True, ""


CATEGORY_INGREDIENT_NAMES = {
    "en:bananas": "Banane",
    "en:cucumbers": "Gurke",
    "en:apples": "Apfel",
    "en:kohlrabi": "Kohlrabi",
    "en:tomatoes": "Tomate",
    "en:avocados": "Avocado",
    "en:zucchini": "Zucchini",
    "en:garlic": "Knoblauch",
    "en:scallions": "Frühlingszwiebel",
    "en:carrots": "Karotte",
    "en:cabbages": "Kohl",
    "en:cauliflowers": "Blumenkohl",
    "en:lettuces": "Blattsalat",
    "en:ginger": "Ingwer",
    "en:mangoes": "Mango",
    "en:leeks": "Lauch",
    "en:radishes": "Radieschen",
    "en:aubergines": "Aubergine",
    "en:sweet-potatoes": "Süßkartoffel",
    "en:fennel-bulbs": "Fenchel",
    "en:pineapple": "Ananas",
    "en:pumpkins": "Kürbis",
    "en:potatoes": "Kartoffel",
    "en:cherry-tomatoes": "Tomate",
    "en:raspberries": "Himbeere",
    "en:mushrooms": "Champignon",
    "en:broccoli": "Brokkoli",
    "en:strawberries": "Erdbeere",
    "en:onions": "Zwiebel",
    "en:blueberries": "Blaubeere",
    "en:kiwis": "Kiwi",
    "en:chicken-eggs": "Ei",
    "en:lemons": "Zitrone",
    "en:plums": "Pflaume",
    "en:pears": "Birne",
    "en:oranges": "Orange",
    "en:asparagus": "Spargel",
    "en:nectarines": "Nektarine",
    "en:chili-peppers": "Chilischote",
    "en:pork-tenderloin": "Schweinefilet",
    "en:beef-steaks": "Rindersteak",
    "en:chicken-breasts": "Hähnchenbrust",
}


# Durchschnittliches essbares Gewicht pro Stück. Diese Werte werden nur für
# die Vorschau und automatische Schätzung verwendet, wenn der Nutzer bewusst
# "Stück" statt einer Gewichtsangabe auswählt.
AVERAGE_UNIT_WEIGHT_GRAMS = {
    "Banane": Decimal("120"),
    "Apfel": Decimal("180"),
    "Birne": Decimal("180"),
    "Orange": Decimal("150"),
    "Mandarine": Decimal("80"),
    "Zitrone": Decimal("80"),
    "Kiwi": Decimal("75"),
    "Avocado": Decimal("150"),
    "Tomate": Decimal("120"),
    "Kartoffel": Decimal("150"),
    "Süßkartoffel": Decimal("250"),
    "Zwiebel": Decimal("100"),
    "Karotte": Decimal("80"),
    "Gurke": Decimal("350"),
    "Zucchini": Decimal("200"),
    "Paprika": Decimal("150"),
    "Chilischote": Decimal("15"),
    "Ei": Decimal("60"),
    "Hähnchenbrust": Decimal("180"),
}


def ingredient_quantity_grams(name, quantity, unit):
    try:
        amount = Decimal(str(quantity))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if amount <= 0:
        return None

    normalized_unit = str(unit or "").strip().casefold()
    factor = {
        "g": Decimal("1"),
        "kg": Decimal("1000"),
        "ml": Decimal("1"),
        "l": Decimal("1000"),
        "liter": Decimal("1000"),
        "el": Decimal("15"),
        "esslöffel": Decimal("15"),
        "tl": Decimal("5"),
        "teelöffel": Decimal("5"),
        "prise": Decimal("0.35"),
    }.get(normalized_unit)
    if factor is not None:
        return amount * factor

    if normalized_unit in {"stück", "stueck"}:
        canonical_name = canonical_recipe_name(name)
        average_weight = AVERAGE_UNIT_WEIGHT_GRAMS.get(canonical_name)
        return amount * average_weight if average_weight is not None else None
    return None
