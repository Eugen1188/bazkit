import re
from decimal import Decimal, InvalidOperation

from .ingredient_catalog import (
    canonical_query,
    curated_canonical_name,
    definition_for_query,
    definition_for_product,
)


AMOUNT_SUFFIX = re.compile(
    r"(?:\s*[,\-–|/]?\s*|\s*\(\s*)"
    r"(?:\d+\s*[x×]\s*)?\d+(?:[.,]\d+)?\s*"
    r"(?:mg|g|kg|ml|cl|dl|l|liter)\b"
    r"(?:\s*(?:packung|flasche|dose|beutel|glas))?\s*\)?\s*$",
    re.I,
)

CANONICAL_RULES = (
    (re.compile(r"^(?:(?:star\s+)?aniseeds?\s+)?sternanis\b|^star\s+anise\b", re.I), "Sternanis"),
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
    r"schupfnudeln|frikadelle|(?:speise)?eis|eiscreme|glace|nougat)\b",
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
COMPOSITE_NON_INGREDIENT = re.compile(
    r"(?:torte|kuchen|muffin|keks|plätzchen|praline|riegel|bonbon|pudding|"
    r"punsch|schorle|cocktail)\b",
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
    if definition_for_product(source, external_id):
        return True, ""
    if PREPARED_FOOD.search(searchable):
        return False, "Fertiggericht oder zusammengesetzte Speise"
    if COMPOSITE_NON_INGREDIENT.search(cleaned_name):
        return False, "Zusammengesetztes Produkt statt Kochzutat"
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


# Durchschnittliches essbares Gewicht pro natürlicher Einzeleinheit. Je nach
# Zutat wird daraus Stück, Stange, Kopf, Zehe, Blatt, Kugel oder Würfel.
AVERAGE_UNIT_WEIGHT_GRAMS = {
    # Obst (durchschnittlicher essbarer Anteil)
    "Acerola": Decimal("5"),
    "Banane": Decimal("120"),
    "Apfel": Decimal("180"),
    "Birne": Decimal("180"),
    "Orange": Decimal("150"),
    "Mandarine": Decimal("80"),
    "Zitrone": Decimal("80"),
    "Limette": Decimal("65"),
    "Kiwi": Decimal("75"),
    "Avocado": Decimal("150"),
    "Mango": Decimal("200"),
    "Ananas": Decimal("900"),
    "Granatapfel": Decimal("280"),
    "Pfirsich": Decimal("150"),
    "Nektarine": Decimal("140"),
    "Aprikose": Decimal("35"),
    "Pflaume": Decimal("70"),
    "Feige": Decimal("50"),
    "Dattel": Decimal("8"),
    "Physalis": Decimal("5"),
    "Zimt": Decimal("3"),
    "Sternanis": Decimal("1.5"),
    "Getrocknete Äpfel": Decimal("5"),
    "Trockenpflaume": Decimal("10"),

    # Gemüse
    "Tomate": Decimal("120"),
    "Kartoffel": Decimal("150"),
    "Süßkartoffel": Decimal("250"),
    "Zwiebel": Decimal("100"),
    "Schalotte": Decimal("25"),
    "Frühlingszwiebel": Decimal("15"),
    # Bei der Suche nach Knoblauchzehe bezeichnet ein Stück eine Zehe,
    # nicht die ganze Knolle.
    "Knoblauch": Decimal("3"),
    "Karotte": Decimal("80"),
    "Pastinake": Decimal("120"),
    "Rote Bete": Decimal("150"),
    "Steckrübe": Decimal("600"),
    "Gurke": Decimal("350"),
    "Zucchini": Decimal("200"),
    "Aubergine": Decimal("300"),
    "Paprika": Decimal("150"),
    "Paprika rot": Decimal("150"),
    "Paprika gelb": Decimal("150"),
    "Paprika grün": Decimal("150"),
    "Chilischote": Decimal("15"),
    "Jalapeño": Decimal("15"),
    "Staudensellerie": Decimal("40"),
    "Knollensellerie": Decimal("500"),
    "Fenchel": Decimal("250"),
    "Kohlrabi": Decimal("350"),
    "Brokkoli": Decimal("400"),
    "Blumenkohl": Decimal("700"),
    "Pak Choi": Decimal("250"),
    "Chinakohl": Decimal("800"),
    "Artischocke": Decimal("300"),
    "Lauch": Decimal("200"),
    "Radieschen": Decimal("15"),
    "Rettich": Decimal("350"),
    "Spargel": Decimal("20"),
    "Champignon": Decimal("20"),
    "Gewürzgurke": Decimal("60"),
    "Ingwer": Decimal("20"),
    "Okra": Decimal("15"),
    "Rosenkohl": Decimal("20"),
    "Topinambur": Decimal("75"),
    "Eisbergsalat": Decimal("500"),
    "Kopfsalat": Decimal("350"),
    "Rotkohl": Decimal("1500"),
    "Weißkohl": Decimal("1200"),
    "Hokkaidokürbis": Decimal("1200"),
    "Kürbis": Decimal("1000"),

    # Tierische Zutaten, wenn Nutzer statt Gramm bewusst Stück wählen
    "Ei": Decimal("60"),
    "Eigelb": Decimal("17"),
    "Eiklar": Decimal("33"),
    "Hähnchenbrust": Decimal("180"),
    "Putenbrust": Decimal("180"),
    "Lachs": Decimal("150"),
    "Wildlachs": Decimal("150"),
    "Seelachs": Decimal("150"),
    "Alaska-Seelachs": Decimal("150"),
    "Kabeljau": Decimal("150"),

    # Küchenformen mit eindeutigem, etabliertem Einzelmaß
    "Frischhefe": Decimal("42"),
    "Gewürznelke": Decimal("0.2"),
    "Lorbeerblatt": Decimal("0.2"),
    "Mozzarella": Decimal("125"),
    "Nori": Decimal("2.5"),
}

CURATED_CONVERSION_SOURCE = "Bazkit kuratierte Portionsreferenz v1"

LOGICAL_UNIT_OVERRIDES = {
    "Knoblauch": "Zehe",
    "Staudensellerie": "Stange",
    "Spargel": "Stange",
    "Lauch": "Stange",
    "Frühlingszwiebel": "Stange",
    "Eisbergsalat": "Kopf",
    "Kopfsalat": "Kopf",
    "Chinakohl": "Kopf",
    "Rotkohl": "Kopf",
    "Weißkohl": "Kopf",
    "Getrocknete Äpfel": "Scheibe",
    "Frischhefe": "Würfel",
    "Lorbeerblatt": "Stück",
    "Mozzarella": "Kugel",
    "Nori": "Blatt",
    "Zimt": "Stange",
}

CURATED_PACKAGE_CONVERSIONS = {
    "Dosentomaten": (("Dose", Decimal("400")),),
    "Passierte Tomaten": (("Packung", Decimal("500")),),
    "Kokosmilch": (("Dose", Decimal("400")),),
    "Kichererbsen": (("Dose", Decimal("400")),),
    "Kidneybohnen": (("Dose", Decimal("400")),),
    "Weiße Bohnen": (("Dose", Decimal("400")),),
    "Dosenmais": (("Dose", Decimal("300")),),
    "Thunfisch": (("Dose", Decimal("150")),),
    "Sahne": (("Becher", Decimal("200")),),
    "Naturjoghurt": (("Becher", Decimal("150")),),
    "Magerquark": (("Packung", Decimal("250")),),
    "Crème fraîche": (("Becher", Decimal("200")),),
    "Saure Sahne": (("Becher", Decimal("200")),),
    "Schmand": (("Becher", Decimal("200")),),
    "Feta": (("Packung", Decimal("200")),),
    "Butter": (("Packung", Decimal("250")),),
    "Tofu": (("Packung", Decimal("200")),),
    "Trockenhefe": (("Packung", Decimal("7")),),
    "Gartenkresse": (("Packung", Decimal("15")),),

    # Rückwärtskompatibilität für ältere, noch nicht normalisierte Namen.
    "Kichererbse": (("Dose", Decimal("400")),),
    "Kidneybohne": (("Dose", Decimal("400")),),
    "Joghurt": (("Becher", Decimal("150")),),
    "Quark": (("Packung", Decimal("250")),),
}

# Dichtewerte verbinden Volumenangaben mit den Nährwerten pro 100 g. Für
# Brühen und Fonds gilt näherungsweise 1 g/ml; Öle, Milch und Sirup erhalten
# ihren produkttypischen Faktor.
LIQUID_DENSITY_GRAMS_PER_ML = {
    "Ahornsirup": Decimal("1.33"),
    "Apfelessig": Decimal("1.01"),
    "Apfelsaft": Decimal("1.04"),
    "Balsamicoessig": Decimal("1.05"),
    "Buttermilch": Decimal("1.03"),
    "Fettarme Milch": Decimal("1.03"),
    "Fischbrühe": Decimal("1"),
    "Fischsauce": Decimal("1.20"),
    "Fleischfond": Decimal("1"),
    "Gemüsebrühe": Decimal("1"),
    "Hühnerbrühe": Decimal("1"),
    "Kokosmilch": Decimal("1.01"),
    "Kokoswasser": Decimal("1"),
    "Milch": Decimal("1.03"),
    "Olivenöl": Decimal("0.91"),
    "Orangensaft": Decimal("1.04"),
    "Passierte Tomaten": Decimal("1.04"),
    "Portwein": Decimal("0.99"),
    "Rapsöl": Decimal("0.92"),
    "Rinderbrühe": Decimal("1"),
    "Rotwein trocken": Decimal("0.99"),
    "Sahne": Decimal("0.99"),
    "Sherry trocken": Decimal("0.99"),
    "Sojasauce": Decimal("1.16"),
    "Sonnenblumenöl": Decimal("0.92"),
    "Tomatensaft": Decimal("1.04"),
    "Vanilleextrakt": Decimal("0.88"),
    "Weißwein trocken": Decimal("0.99"),
}

# Flüssige Zutaten, die in Rezepten zusätzlich häufig löffelweise dosiert
# werden. TL und EL werden anhand der oben gepflegten Dichte berechnet.
LIQUID_SPOON_INGREDIENTS = {
    "Ahornsirup", "Apfelessig", "Balsamicoessig", "Fischsauce",
    "Olivenöl", "Rapsöl", "Sahne", "Sojasauce", "Sonnenblumenöl",
    "Vanilleextrakt",
}

# Redaktionell gepflegte Küchenmaße für trockene, cremige und gebündelte
# Zutaten. Jeder angebotenen Einheit ist ein Grammwert zugeordnet, damit sie
# niemals nur auswählbar ist, ohne in die Nährwertberechnung einzugehen.
CURATED_KITCHEN_CONVERSIONS = {
    # Frische Kräuter und typische Bündel
    "Basilikum": (("Bund", Decimal("30")),),
    "Dill": (("Bund", Decimal("20")),),
    "Koriander": (("Bund", Decimal("30")),),
    "Petersilie": (("Bund", Decimal("30")),),
    "Rosmarin": (("Bund", Decimal("20")),),
    "Salbei": (("Bund", Decimal("20")),),
    "Schnittlauch": (("Bund", Decimal("30")),),
    "Thymian": (("Bund", Decimal("20")),),
    "Frühlingszwiebel": (("Bund", Decimal("100")),),
    "Radieschen": (("Bund", Decimal("250")),),

    # Gewürze, Backtriebmittel und trockene Kräuter
    "Backpulver": (("TL", Decimal("4")), ("EL", Decimal("12"))),
    "Basilikum getrocknet": (("TL", Decimal("1.4")), ("EL", Decimal("4.2")), ("Prise", Decimal("0.1"))),
    "Fenchelsamen": (("TL", Decimal("2")), ("EL", Decimal("6"))),
    "Kakaopulver": (("TL", Decimal("2.5")), ("EL", Decimal("7.5"))),
    "Kardamom": (("TL", Decimal("2")), ("EL", Decimal("6")), ("Prise", Decimal("0.1"))),
    "Koriandersamen": (("TL", Decimal("1.8")), ("EL", Decimal("5.4"))),
    "Kreuzkümmel": (("TL", Decimal("2.1")), ("EL", Decimal("6.3")), ("Prise", Decimal("0.15"))),
    "Kurkuma": (("TL", Decimal("3")), ("EL", Decimal("9")), ("Prise", Decimal("0.2"))),
    "Majoran": (("TL", Decimal("0.6")), ("EL", Decimal("1.8")), ("Prise", Decimal("0.05"))),
    "Muskatnuss": (("TL", Decimal("2.2")), ("EL", Decimal("6.6")), ("Prise", Decimal("0.1"))),
    "Natron": (("TL", Decimal("5")), ("EL", Decimal("15"))),
    "Oregano": (("TL", Decimal("1")), ("EL", Decimal("3")), ("Prise", Decimal("0.08"))),
    "Paprikapulver": (("TL", Decimal("2.3")), ("EL", Decimal("7")), ("Prise", Decimal("0.2"))),
    "Rosmarin getrocknet": (("TL", Decimal("1.2")), ("EL", Decimal("3.6")), ("Prise", Decimal("0.1"))),
    "Safran": (("Prise", Decimal("0.1")),),
    "Salz": (("TL", Decimal("5")), ("EL", Decimal("15")), ("Prise", Decimal("0.3"))),
    "Schwarzer Pfeffer": (("TL", Decimal("2.3")), ("EL", Decimal("7")), ("Prise", Decimal("0.1"))),
    "Thymian getrocknet": (("TL", Decimal("1")), ("EL", Decimal("3")), ("Prise", Decimal("0.08"))),
    "Zimt": (("TL", Decimal("2.6")), ("EL", Decimal("7.8")), ("Prise", Decimal("0.2"))),
    "Sternanis": (("TL", Decimal("2")), ("EL", Decimal("6"))),

    # Samen, Kerne und feine trockene Zutaten
    "Chiasamen": (("TL", Decimal("4")), ("EL", Decimal("12"))),
    "Kürbiskerne": (("TL", Decimal("3.3")), ("EL", Decimal("10"))),
    "Leinsamen": (("TL", Decimal("3")), ("EL", Decimal("9"))),
    "Mohn": (("TL", Decimal("3")), ("EL", Decimal("9"))),
    "Senfkörner": (("TL", Decimal("3.1")), ("EL", Decimal("9.3"))),
    "Sesam": (("TL", Decimal("3")), ("EL", Decimal("9"))),
    "Sonnenblumenkerne": (("TL", Decimal("3")), ("EL", Decimal("9"))),

    # Mehle, Stärke, Getreide und übliche Tassenmaße
    "Amaranth": (("Tasse", Decimal("190")),),
    "Buchweizen": (("Tasse", Decimal("170")),),
    "Bulgur": (("Tasse", Decimal("180")),),
    "Couscous": (("Tasse", Decimal("170")),),
    "Dinkelmehl Type 630": (("TL", Decimal("3.3")), ("EL", Decimal("10")), ("Tasse", Decimal("120"))),
    "Haferflocken": (("EL", Decimal("8")), ("Tasse", Decimal("80"))),
    "Hirse": (("Tasse", Decimal("200")),),
    "Maisstärke": (("TL", Decimal("3")), ("EL", Decimal("9"))),
    "Quinoa": (("Tasse", Decimal("170")),),
    "Reis": (("Tasse", Decimal("200")),),
    "Roggenmehl Type 1150": (("TL", Decimal("3.3")), ("EL", Decimal("10")), ("Tasse", Decimal("120"))),
    "Weizenmehl Type 405": (("TL", Decimal("3.3")), ("EL", Decimal("10")), ("Tasse", Decimal("120"))),
    "Zucker": (("TL", Decimal("4")), ("EL", Decimal("12")), ("Tasse", Decimal("200"))),

    # Cremige Zutaten, Pasten und weitere gebräuchliche Küchenmaße
    "Butter": (("TL", Decimal("5")), ("EL", Decimal("14"))),
    "Crème fraîche": (("TL", Decimal("5")), ("EL", Decimal("15"))),
    "Erdnussbutter": (("TL", Decimal("5.3")), ("EL", Decimal("16"))),
    "Gelatine": (("Blatt", Decimal("1.7")), ("TL", Decimal("3"))),
    "Magerquark": (("EL", Decimal("15")),),
    "Meerrettich": (("TL", Decimal("5")), ("EL", Decimal("15"))),
    "Miso": (("TL", Decimal("6")), ("EL", Decimal("18"))),
    "Naturjoghurt": (("TL", Decimal("5")), ("EL", Decimal("15"))),
    "Sambal Oelek": (("TL", Decimal("5")), ("EL", Decimal("15"))),
    "Saure Sahne": (("TL", Decimal("5")), ("EL", Decimal("15"))),
    "Schmand": (("TL", Decimal("5")), ("EL", Decimal("15"))),
    "Tahini": (("TL", Decimal("5")), ("EL", Decimal("15"))),
    "Tomatenmark": (("TL", Decimal("5")), ("EL", Decimal("15"))),
    "Trockenhefe": (("TL", Decimal("3")), ("EL", Decimal("9"))),
}

# Bei diesen Zutaten ist ein Kilogramm als Rezeptmaß unüblich. Sie behalten
# Gramm sowie ihre ausdrücklich gepflegten Küchenmaße.
GRAM_ONLY_INGREDIENTS = {
    "Backpulver", "Basilikum", "Basilikum getrocknet", "Dill",
    "Fenchelsamen", "Frischhefe", "Gartenkresse", "Gelatine",
    "Gewürznelke", "Kakaopulver", "Kardamom", "Koriander",
    "Koriandersamen", "Kreuzkümmel", "Kurkuma", "Lorbeerblatt",
    "Majoran", "Maisstärke", "Muskatnuss", "Natron", "Nori", "Oregano",
    "Paprikapulver", "Petersilie", "Rosmarin", "Rosmarin getrocknet",
    "Safran", "Salbei", "Salz", "Schnittlauch", "Schwarzer Pfeffer",
    "Senfkörner", "Sternanis", "Thymian", "Thymian getrocknet",
    "Trockenhefe", "Vanilleextrakt", "Zimt",
}

UNIT_DISPLAY_ORDER = {
    unit: index
    for index, unit in enumerate((
        "Stück", "Stange", "Kopf", "Blatt", "Kugel", "Würfel", "Zehe",
        "Scheibe", "Bund", "TL", "EL", "Prise", "Tasse", "Packung",
        "Dose", "Glas", "Becher",
    ))
}


def canonical_unit_name(name):
    raw_name = str(name or "").strip()
    canonical_name = canonical_query(raw_name)
    if canonical_name == raw_name:
        canonical_name = canonical_recipe_name(raw_name)
    return canonical_name


def average_unit_weight_grams(name):
    return AVERAGE_UNIT_WEIGHT_GRAMS.get(canonical_unit_name(name))


def liquid_density_grams_per_ml(name):
    return LIQUID_DENSITY_GRAMS_PER_ML.get(canonical_unit_name(name))


def _is_known_unit_name(unit_name):
    return (
        definition_for_query(unit_name) is not None
        or unit_name in AVERAGE_UNIT_WEIGHT_GRAMS
        or unit_name in CURATED_PACKAGE_CONVERSIONS
        or unit_name in CURATED_KITCHEN_CONVERSIONS
        or unit_name in LIQUID_DENSITY_GRAMS_PER_ML
    )


def resolved_product_unit_name(
    name,
    canonical_name="",
    source="",
    external_id="",
):
    definition = definition_for_product(source, external_id, canonical_name)
    if definition is not None:
        return definition.canonical_name
    for candidate in (name, canonical_name):
        if not str(candidate or "").strip():
            continue
        unit_name = canonical_unit_name(candidate)
        if _is_known_unit_name(unit_name):
            return unit_name
    return canonical_unit_name(canonical_name or name)


def has_curated_unit_profile(name):
    unit_name = canonical_unit_name(name)
    return _is_known_unit_name(unit_name)


def curated_unit_conversions(name):
    """Liefert redaktionell gepflegte Küchen- und Packungsumrechnungen."""
    canonical_name = canonical_unit_name(name)
    conversions = []
    grams = average_unit_weight_grams(name)
    if grams is not None:
        conversions.append({
            "unit": LOGICAL_UNIT_OVERRIDES.get(canonical_name, "Stück"),
            "grams_per_unit": grams,
            "source": CURATED_CONVERSION_SOURCE,
            "confidence": "reference",
        })
    for unit, package_grams in CURATED_PACKAGE_CONVERSIONS.get(canonical_name, ()):
        conversions.append({
            "unit": unit,
            "grams_per_unit": package_grams,
            "source": CURATED_CONVERSION_SOURCE,
            "confidence": "reference",
        })
    for unit, kitchen_grams in CURATED_KITCHEN_CONVERSIONS.get(canonical_name, ()):
        conversions.append({
            "unit": unit,
            "grams_per_unit": kitchen_grams,
            "source": CURATED_CONVERSION_SOURCE,
            "confidence": "reference",
        })
    if canonical_name in LIQUID_SPOON_INGREDIENTS:
        density = LIQUID_DENSITY_GRAMS_PER_ML[canonical_name]
        for unit, milliliters in (("TL", Decimal("5")), ("EL", Decimal("15"))):
            conversions.append({
                "unit": unit,
                "grams_per_unit": density * milliliters,
                "source": CURATED_CONVERSION_SOURCE,
                "confidence": "reference",
            })
    return conversions


def curated_unit_conversion(name):
    conversions = curated_unit_conversions(name)
    return conversions[0] if conversions else None


def product_unit_conversions(
    name,
    canonical_name="",
    package_quantity=None,
    package_unit="",
    source="",
    external_id="",
):
    """Liefert alle belastbaren Umrechnungen auch für noch ungespeicherte Treffer."""
    unit_name = resolved_product_unit_name(
        name,
        canonical_name,
        source,
        external_id,
    )
    conversions = curated_unit_conversions(unit_name)
    package_factor = {
        "mg": Decimal("0.001"), "g": Decimal("1"), "kg": Decimal("1000"),
        "ml": Decimal("1"), "cl": Decimal("10"), "dl": Decimal("100"),
        "l": Decimal("1000"),
    }.get(str(package_unit or "").casefold())
    try:
        package_amount = Decimal(str(package_quantity)) if package_quantity is not None else None
    except (InvalidOperation, TypeError, ValueError):
        package_amount = None
    if package_amount and package_amount > 0 and package_factor is not None:
        package_label = next(
            (label for label in ("Dose", "Glas", "Becher") if label.casefold() in str(name or "").casefold()),
            "Packung",
        )
        conversions = [conversion for conversion in conversions if conversion["unit"] != package_label]
        conversions.append({
            "unit": package_label,
            "grams_per_unit": package_amount * package_factor,
            "source": "Open Food Facts Packungsangabe",
            "confidence": "verified",
        })
    return conversions


def logical_available_units(
    default_unit="",
    package_unit="",
    shopping_category="",
    conversions=(),
    canonical_name="",
):
    unit_name = canonical_unit_name(canonical_name)
    metadata_is_liquid = (
        str(default_unit or "").casefold() in {"ml", "l", "liter"}
        or str(package_unit or "").casefold() in {"ml", "l"}
        or shopping_category == "drinks"
    )
    is_liquid = (
        unit_name in LIQUID_DENSITY_GRAMS_PER_ML
        or (not has_curated_unit_profile(unit_name) and metadata_is_liquid)
    )
    if is_liquid:
        units = ["ml", "Liter"]
    elif unit_name in GRAM_ONLY_INGREDIENTS:
        units = ["g"]
    else:
        units = ["g", "kg"]
    for conversion in sorted(
        conversions,
        key=lambda item: UNIT_DISPLAY_ORDER.get(
            item["unit"] if isinstance(item, dict) else item.unit,
            len(UNIT_DISPLAY_ORDER),
        ),
    ):
        unit = conversion["unit"] if isinstance(conversion, dict) else conversion.unit
        if unit not in units:
            units.append(unit)
    return units


def sync_curated_unit_conversion(product):
    from .models import ProductUnitConversion

    conversions = product_unit_conversions(
        product.name,
        product.canonical_name,
        product.package_quantity,
        product.package_unit,
        product.source,
        product.external_id,
    )
    if not conversions:
        ProductUnitConversion.objects.filter(
            product=product,
            source__in=(CURATED_CONVERSION_SOURCE, "Open Food Facts Packungsangabe"),
        ).delete()
        return None
    desired_units = {conversion["unit"] for conversion in conversions}
    ProductUnitConversion.objects.filter(
        product=product,
        source__in=(CURATED_CONVERSION_SOURCE, "Open Food Facts Packungsangabe"),
    ).exclude(unit__in=desired_units).delete()
    values = []
    for conversion in conversions:
        value, _created = ProductUnitConversion.objects.update_or_create(
            product=product,
            unit=conversion["unit"],
            defaults={
                "grams_per_unit": conversion["grams_per_unit"],
                "source": conversion["source"],
                "confidence": conversion["confidence"],
                "is_active": True,
            },
        )
        values.append(value)
    return values


def suggested_unit_for_product(
    name,
    canonical_name="",
    shopping_category="",
    fallback_unit="g",
):
    unit_name = resolved_product_unit_name(name, canonical_name)
    if (
        unit_name in LIQUID_DENSITY_GRAMS_PER_ML
        or (not has_curated_unit_profile(unit_name) and shopping_category == "drinks")
    ):
        return "ml"
    if unit_name in AVERAGE_UNIT_WEIGHT_GRAMS:
        return LOGICAL_UNIT_OVERRIDES.get(unit_name, "Stück")
    packages = CURATED_PACKAGE_CONVERSIONS.get(unit_name, ())
    if packages:
        return packages[0][0]
    available_units = logical_available_units(
        fallback_unit,
        "",
        shopping_category,
        curated_unit_conversions(unit_name),
        unit_name,
    )
    fallback = "Liter" if str(fallback_unit or "").casefold() in {"l", "liter"} else str(fallback_unit or "g")
    return fallback if fallback in available_units else available_units[0]


def ingredient_quantity_grams(name, quantity, unit, product=None):
    try:
        amount = Decimal(str(quantity))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if amount <= 0:
        return None

    normalized_unit = str(unit or "").strip().casefold()
    weight_factor = {
        "g": Decimal("1"),
        "kg": Decimal("1000"),
    }.get(normalized_unit)
    if weight_factor is not None:
        return amount * weight_factor

    volume_factor = {
        "ml": Decimal("1"),
        "l": Decimal("1000"),
        "liter": Decimal("1000"),
    }.get(normalized_unit)
    if volume_factor is not None:
        density_name = (
            resolved_product_unit_name(
                product.name,
                product.canonical_name,
                product.source,
                product.external_id,
            )
            if product is not None
            else name
        )
        density = liquid_density_grams_per_ml(density_name) or Decimal("1")
        return amount * volume_factor * density

    if product is not None:
        conversion = product.unit_conversions.filter(
            unit__iexact=str(unit or "").strip(), is_active=True
        ).exclude(confidence="estimated").first()
        if conversion is not None:
            return amount * conversion.grams_per_unit
        conversion = next(
            (
                item for item in curated_unit_conversions(
                    resolved_product_unit_name(
                        product.name,
                        product.canonical_name,
                        product.source,
                        product.external_id,
                    )
                )
                if item["unit"].casefold() == normalized_unit
                and item["confidence"] != "estimated"
            ),
            None,
        )
        if conversion is not None:
            return amount * conversion["grams_per_unit"]
    else:
        conversion = next(
            (
                item for item in curated_unit_conversions(name)
                if item["unit"].casefold() == normalized_unit
            ),
            None,
        )
        if conversion is not None:
            return amount * conversion["grams_per_unit"]
    return None
