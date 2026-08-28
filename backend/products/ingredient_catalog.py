import re
from dataclasses import dataclass


@dataclass(frozen=True)
class IngredientDefinition:
    canonical_name: str
    aliases: tuple[str, ...]
    usda_query: str


# Die Liste bildet die Sprache ab, die Nutzer beim Kochen tatsächlich verwenden.
# Sie ersetzt keine Nährwertquelle: Sie führt lediglich Schreibweisen und
# Einkaufsbegriffe auf einen eindeutigen, generischen Zutatenbegriff zurück.
INGREDIENT_DEFINITIONS = (
    IngredientDefinition("Dosentomaten", ("dosentomaten", "tomaten aus der dose", "tomaten in der dose", "gehackte tomaten", "stückige tomaten", "tomaten stückig", "tomaten gehackt", "tomaten konserve", "konservierte tomaten"), "tomatoes canned red ripe"),
    IngredientDefinition("Passierte Tomaten", ("passierte tomaten", "tomaten passiert", "tomatenpassata", "passata"), "tomato puree canned"),
    IngredientDefinition("Tomatenmark", ("tomatenmark", "tomaten paste", "tomatenpaste"), "tomato paste canned"),
    IngredientDefinition("Tomatensaft", ("tomatensaft", "tomaten saft"), "tomato juice canned"),
    IngredientDefinition("Tomate", ("tomate", "tomaten", "strauchtomate", "strauchtomaten", "fleischtomate", "fleischtomaten", "cherrytomate", "cherrytomaten", "kirschtomate", "kirschtomaten"), "tomatoes red ripe raw"),
    IngredientDefinition("Chilischote", ("chilischote", "chilischoten", "chili", "chilis", "chilli", "chillis", "chilischotten", "peperoni", "peperonischote", "rote chili"), "peppers hot chili red raw"),
    IngredientDefinition("Paprika", ("paprika", "paprikaschote", "paprikaschoten", "gemüsepaprika", "rote paprika", "gelbe paprika", "grüne paprika"), "peppers sweet red raw"),
    IngredientDefinition("Zwiebel", ("zwiebel", "zwiebeln", "speisezwiebel", "gemüsezwiebel", "rote zwiebel"), "onions raw"),
    IngredientDefinition("Frühlingszwiebel", ("frühlingszwiebel", "frühlingszwiebeln", "lauchzwiebel", "lauchzwiebeln", "spring onion"), "onions spring raw"),
    IngredientDefinition("Knoblauch", ("knoblauch", "knoblauchzehe", "knoblauchzehen"), "garlic raw"),
    IngredientDefinition("Kartoffel", ("kartoffel", "kartoffeln", "speisekartoffel", "erdapfel"), "potatoes flesh and skin raw"),
    IngredientDefinition("Süßkartoffel", ("süßkartoffel", "süßkartoffeln", "suesskartoffel", "batate"), "sweet potato raw unprepared"),
    IngredientDefinition("Karotte", ("karotte", "karotten", "möhre", "möhren", "gelbe rübe", "wurzel"), "carrots raw"),
    IngredientDefinition("Gurke", ("gurke", "gurken", "salatgurke", "schlangengurke"), "cucumber with peel raw"),
    IngredientDefinition("Zucchini", ("zucchini", "zucchinis", "zucchino"), "squash summer zucchini raw"),
    IngredientDefinition("Aubergine", ("aubergine", "auberginen", "eierfrucht"), "eggplant raw"),
    IngredientDefinition("Brokkoli", ("brokkoli", "broccoli"), "broccoli raw"),
    IngredientDefinition("Blumenkohl", ("blumenkohl", "karfiol"), "cauliflower raw"),
    IngredientDefinition("Spinat", ("spinat", "blattspinat", "babyspinat", "tiefkühlspinat", "tk spinat"), "spinach raw"),
    IngredientDefinition("Champignon", ("champignon", "champignons", "pilz", "pilze", "kulturchampignon"), "mushrooms white raw"),
    IngredientDefinition("Lauch", ("lauch", "porree"), "leeks raw"),
    IngredientDefinition("Sellerie", ("sellerie", "knollensellerie", "stangensellerie", "staudensellerie"), "celery raw"),
    IngredientDefinition("Mais", ("mais", "dosenmais", "mais aus der dose", "zuckermais"), "corn sweet yellow canned"),
    IngredientDefinition("Erbse", ("erbse", "erbsen", "tiefkühlerbsen", "tk erbsen"), "peas green frozen unprepared"),
    IngredientDefinition("Kidneybohnen", ("kidneybohne", "kidneybohnen", "rote bohnen", "rote bohnen dose"), "beans kidney canned"),
    IngredientDefinition("Weiße Bohnen", ("weiße bohnen", "weisse bohnen", "cannellini", "cannellinibohnen"), "beans white canned"),
    IngredientDefinition("Kichererbsen", ("kichererbse", "kichererbsen", "kichererbsen dose", "garbanzobohnen"), "chickpeas canned"),
    IngredientDefinition("Linsen", ("linse", "linsen", "braune linsen", "grüne linsen", "rote linsen", "berg-linsen"), "lentils mature seeds cooked"),
    IngredientDefinition("Milch", ("milch", "kuhmilch", "vollmilch", "frischmilch", "h milch", "h-milch", "fettarme milch"), "milk whole 3.25% milkfat"),
    IngredientDefinition("Buttermilch", ("buttermilch", "reine buttermilch"), "buttermilk fluid cultured lowfat"),
    IngredientDefinition("Sahne", ("sahne", "schlagsahne", "schlagrahm", "rahm", "süße sahne", "kochcreme"), "cream fluid heavy whipping"),
    IngredientDefinition("Saure Sahne", ("saure sahne", "sauerrahm", "sour cream", "schmand"), "sour cream cultured"),
    IngredientDefinition("Crème fraîche", ("crème fraîche", "creme fraiche", "creme fraîche"), "creme fraiche"),
    IngredientDefinition("Naturjoghurt", ("naturjoghurt", "joghurt natur", "jogurt natur", "joghurt", "yoghurt"), "yogurt plain whole milk"),
    IngredientDefinition("Magerquark", ("magerquark", "quark mager", "speisequark mager", "quark"), "quark low fat"),
    IngredientDefinition("Butter", ("butter", "süßrahmbutter", "sauerrahmbutter"), "butter salted"),
    IngredientDefinition("Ei", ("ei", "eier", "hühnerei", "hühnereier", "vollei"), "egg whole raw fresh"),
    IngredientDefinition("Hähnchenbrust", ("hähnchenbrust", "hähnchenbrustfilet", "hühnerbrust", "huhn brust", "chicken breast"), "chicken breast meat only raw"),
    IngredientDefinition("Putenbrust", ("putenbrust", "putenbrustfilet", "truthahnbrust"), "turkey breast meat only raw"),
    IngredientDefinition("Rinderhackfleisch", ("rinderhackfleisch", "rinderhack", "hackfleisch rind", "gehacktes rind"), "ground beef 90% lean raw"),
    IngredientDefinition("Hackfleisch", ("hackfleisch", "gehacktes", "gemischtes hackfleisch", "hackfleisch gemischt"), "ground beef and pork raw"),
    IngredientDefinition("Lachs", ("lachs", "lachsfilet", "wildlachs"), "salmon atlantic raw"),
    IngredientDefinition("Thunfisch", ("thunfisch", "thunfisch dose", "thunfisch aus der dose", "thunfisch im eigenen saft"), "tuna canned in water drained"),
    IngredientDefinition("Tofu", ("tofu", "naturtofu", "tofu natur", "sojaquark"), "tofu raw firm prepared with calcium"),
    IngredientDefinition("Reis", ("reis", "langkornreis", "basmatireis", "basmati", "jasminreis"), "rice white long grain regular raw"),
    IngredientDefinition("Nudeln", ("nudel", "nudeln", "pasta", "spaghetti", "penne", "fusilli", "makkaroni"), "pasta dry unenriched"),
    IngredientDefinition("Haferflocken", ("haferflocke", "haferflocken", "oats", "porridgeflocken"), "oats regular and quick not fortified dry"),
    IngredientDefinition("Weizenmehl", ("weizenmehl", "mehl", "weißmehl", "weissmehl", "mehl type 405", "mehl 405"), "wheat flour white all-purpose unenriched"),
    IngredientDefinition("Zucker", ("zucker", "haushaltszucker", "kristallzucker", "raffinadezucker"), "sugars granulated"),
    IngredientDefinition("Salz", ("salz", "speisesalz", "kochsalz", "tafelsalz", "jodsalz"), "salt table"),
    IngredientDefinition("Olivenöl", ("olivenöl", "olivenoel", "natives olivenöl", "extra natives olivenöl"), "oil olive salad or cooking"),
    IngredientDefinition("Rapsöl", ("rapsöl", "rapsoel", "canolaöl", "canola oil"), "oil canola"),
    IngredientDefinition("Sonnenblumenöl", ("sonnenblumenöl", "sonnenblumenoel"), "oil sunflower linoleic"),
    IngredientDefinition("Gemüsebrühe", ("gemüsebrühe", "gemüsebruehe", "gemüsefond", "brühwürfel gemüse", "brühe gemüse"), "vegetable broth ready to serve"),
    IngredientDefinition("Apfel", ("apfel", "äpfel", "aepfel", "tafelapfel"), "apples with skin raw"),
    IngredientDefinition("Banane", ("banane", "bananen"), "bananas raw"),
    IngredientDefinition("Zitrone", ("zitrone", "zitronen", "bio zitrone"), "lemons raw without peel"),
)


def normalize_alias(value):
    text = str(value or "").strip().casefold()
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:150]


def _alias_index():
    result = {}
    for definition in INGREDIENT_DEFINITIONS:
        for alias in (definition.canonical_name, *definition.aliases):
            result[normalize_alias(alias)] = definition
    return result


ALIAS_INDEX = _alias_index()
CANONICAL_INDEX = {
    normalize_alias(definition.canonical_name): definition
    for definition in INGREDIENT_DEFINITIONS
}


def definition_for_query(value):
    normalized = normalize_alias(value)
    exact = ALIAS_INDEX.get(normalized)
    if exact:
        return exact
    if len(normalized) < 4:
        return None
    prefix_matches = {
        definition
        for alias, definition in ALIAS_INDEX.items()
        if alias.startswith(normalized)
    }
    return next(iter(prefix_matches)) if len(prefix_matches) == 1 else None


def definition_for_canonical(value):
    return CANONICAL_INDEX.get(normalize_alias(value))


def expanded_search_terms(value):
    definition = definition_for_query(value)
    if not definition:
        return {str(value or "").strip()}
    return {
        str(value or "").strip(),
        definition.canonical_name,
        *definition.aliases,
    }


def canonical_query(value):
    definition = definition_for_query(value)
    return definition.canonical_name if definition else str(value or "").strip()


def usda_query(value):
    definition = definition_for_query(value)
    return definition.usda_query if definition else str(value or "").strip()


def usda_display_name(value, fallback):
    definition = definition_for_query(value)
    return definition.canonical_name if definition else str(fallback or value).strip().title()


def aliases_for_product(name, canonical_name=""):
    values = {}

    def add(alias, source="derived"):
        alias = re.sub(r"\s+", " ", str(alias or "")).strip(" ,-–/")[:150]
        normalized = normalize_alias(alias)
        if normalized and normalized not in values:
            values[normalized] = (alias, source)

    add(name)
    add(canonical_name)
    without_parentheses = re.sub(r"\([^)]*\)", "", str(name or ""))
    add(without_parentheses)
    first_part = without_parentheses.split(",", 1)[0]
    add(first_part)
    if "," in without_parentheses:
        left, right = (part.strip() for part in without_parentheses.split(",", 1))
        add(f"{left} {right}")
        add(f"{right} {left}")

    definition = definition_for_canonical(canonical_name)
    if definition:
        add(definition.canonical_name, "curated")
        for alias in definition.aliases:
            add(alias, "curated")
    return [(alias, normalized, source) for normalized, (alias, source) in values.items()]


def replace_product_aliases(product):
    from .models import ProductAlias

    ProductAlias.objects.filter(product=product).delete()
    ProductAlias.objects.bulk_create([
        ProductAlias(
            product=product,
            alias=alias,
            normalized_alias=normalized,
            source=source,
        )
        for alias, normalized, source in aliases_for_product(
            product.name,
            product.canonical_name,
        )
    ])


def rebuild_product_aliases(products, batch_size=1000):
    from .models import ProductAlias

    product_ids = list(products.values_list("id", flat=True))
    ProductAlias.objects.filter(product_id__in=product_ids).delete()
    pending = []
    for product in products.iterator(chunk_size=500):
        for alias, normalized, source in aliases_for_product(
            product.name,
            product.canonical_name,
        ):
            pending.append(ProductAlias(
                product_id=product.id,
                alias=alias,
                normalized_alias=normalized,
                source=source,
            ))
        if len(pending) >= batch_size:
            ProductAlias.objects.bulk_create(pending, ignore_conflicts=True, batch_size=batch_size)
            pending.clear()
    if pending:
        ProductAlias.objects.bulk_create(pending, ignore_conflicts=True, batch_size=batch_size)
