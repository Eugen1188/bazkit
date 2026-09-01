import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .ingredient_catalog_data import EXTENDED_INGREDIENT_DEFINITIONS


@dataclass(frozen=True)
class IngredientDefinition:
    canonical_name: str
    aliases: tuple[str, ...]
    usda_query: str
    preferred_bls_codes: tuple[str, ...] = ()
    preferred_usda_ids: tuple[str, ...] = ()


# Die Liste bildet die Sprache ab, die Nutzer beim Kochen tatsächlich verwenden.
# Sie ersetzt keine Nährwertquelle: Sie führt lediglich Schreibweisen und
# Einkaufsbegriffe auf einen eindeutigen, generischen Zutatenbegriff zurück.
CORE_INGREDIENT_DEFINITIONS = (
    IngredientDefinition("Dosentomaten", ("dosentomaten", "tomaten aus der dose", "tomaten in der dose", "gehackte tomaten", "stückige tomaten", "tomaten stückig", "tomaten gehackt", "tomaten konserve", "konservierte tomaten", "pizzatomaten"), "tomatoes canned red ripe", ("G560900", "G568900")),
    IngredientDefinition("Passierte Tomaten", ("passierte tomaten", "tomaten passiert", "tomatenpassata", "passata", "tomatenpüree"), "tomato puree canned", ("R161200",)),
    IngredientDefinition("Tomatenmark", ("tomatenmark", "tomaten paste", "tomatenpaste"), "tomato paste canned", ("R160000",)),
    IngredientDefinition("Tomatensaft", ("tomatensaft", "tomaten saft", "gemüsesaft aus tomate"), "tomato juice canned", ("G560600",)),
    IngredientDefinition("Tomate", ("tomate", "tomaten", "strauchtomate", "strauchtomaten", "fleischtomate", "fleischtomaten", "cherrytomate", "cherrytomaten", "kirschtomate", "kirschtomaten", "rispentomate", "rispentomaten"), "tomatoes red ripe raw", ("G561100",)),
    IngredientDefinition("Chilischote", ("chilischote", "chilischoten", "chili", "chilis", "chilli", "chillis", "chilischotten", "peperoni", "peperonischote", "rote chili"), "peppers hot chili red raw", (), ("170497",)),
    IngredientDefinition("Paprika rot", ("rote paprika", "paprika rot", "rote paprikaschote", "roter paprika"), "peppers sweet red raw", ("G543100",)),
    IngredientDefinition("Paprika gelb", ("gelbe paprika", "paprika gelb", "gelbe paprikaschote", "gelber paprika"), "peppers sweet yellow raw", ("G542100",)),
    IngredientDefinition("Paprika grün", ("grüne paprika", "paprika grün", "grüne paprikaschote", "gruene paprika", "grüner paprika"), "peppers sweet green raw", ("G541100",)),
    IngredientDefinition("Paprika", ("paprika", "paprikaschote", "paprikaschoten", "gemüsepaprika"), "peppers sweet red raw", ("G543100", "G542100", "G541100")),
    IngredientDefinition("Zwiebel", ("zwiebel", "zwiebeln", "speisezwiebel", "gemüsezwiebel", "gemüsezwiebeln", "küchenzwiebel", "haushaltszwiebel", "gelbe zwiebel", "weiße zwiebel", "rote zwiebel", "riesenzwiebel", "spanische zwiebel"), "onions raw", ("G480100",)),
    IngredientDefinition("Frühlingszwiebel", ("frühlingszwiebel", "frühlingszwiebeln", "lauchzwiebel", "lauchzwiebeln", "spring onion"), "onions spring raw", ("G482100",)),
    IngredientDefinition("Knoblauch", ("knoblauch", "knoblauchzehe", "knoblauchzehen"), "garlic raw", ("G490100",)),
    IngredientDefinition("Kartoffel", ("kartoffel", "kartoffeln", "speisekartoffel", "erdapfel"), "potatoes flesh and skin raw", ("K110100",)),
    IngredientDefinition("Süßkartoffel", ("süßkartoffel", "süßkartoffeln", "suesskartoffel", "batate"), "sweet potato raw unprepared", ("K420100",)),
    IngredientDefinition("Karotte", ("karotte", "karotten", "möhre", "möhren", "gelbe rübe", "wurzel"), "carrots raw", ("G620100",)),
    IngredientDefinition("Gurke", ("gurke", "gurken", "salatgurke", "schlangengurke"), "cucumber with peel raw", ("G520100",)),
    IngredientDefinition("Zucchini", ("zucchini", "zucchinis", "zucchino"), "squash summer zucchini raw", ("G582100",)),
    IngredientDefinition("Aubergine", ("aubergine", "auberginen", "eierfrucht"), "eggplant raw", ("G510100",)),
    IngredientDefinition("Brokkoli", ("brokkoli", "broccoli"), "broccoli raw", ("G312100",)),
    IngredientDefinition("Blumenkohl", ("blumenkohl", "karfiol"), "cauliflower raw", ("G311100",)),
    IngredientDefinition("Spinat", ("spinat", "blattspinat", "babyspinat", "tiefkühlspinat", "tk spinat"), "spinach raw", ("G211100",)),
    IngredientDefinition("Champignon", ("champignon", "champignons", "pilz", "pilze", "kulturchampignon"), "mushrooms white raw", ("K701100",)),
    IngredientDefinition("Lauch", ("lauch", "porree"), "leeks raw", ("G470100",)),
    IngredientDefinition("Staudensellerie", ("staudensellerie", "stangensellerie", "bleichsellerie", "selleriestange", "selleriestangen", "stangen sellerie"), "celery raw", ("G220100",)),
    IngredientDefinition("Knollensellerie", ("knollensellerie", "sellerieknolle", "sellerie knolle", "wurzel sellerie"), "celeriac raw", ("G660100",)),
    IngredientDefinition("Sellerie", ("sellerie",), "celery raw", ("G220100", "G660100")),
    IngredientDefinition("Dosenmais", ("dosenmais", "mais aus der dose", "zuckermais dose", "mais konserve"), "corn sweet yellow canned", ("G570902",)),
    IngredientDefinition("Mais", ("mais", "zuckermais", "mais frisch"), "corn sweet yellow raw", ("G570100",)),
    IngredientDefinition("Erbse", ("erbse", "erbsen", "tiefkühlerbsen", "tk erbsen"), "peas green frozen unprepared", ("G760200", "G760100")),
    IngredientDefinition("Kidneybohnen", ("kidneybohne", "kidneybohnen", "rote bohnen", "rote bohnen dose"), "beans kidney canned", ("H742902",)),
    IngredientDefinition("Weiße Bohnen", ("weiße bohnen", "weisse bohnen", "cannellini", "cannellinibohnen"), "beans white canned", ("H740902",)),
    IngredientDefinition("Milch", ("milch", "kuhmilch", "vollmilch", "frischmilch", "h milch", "h-milch"), "milk whole 3.25% milkfat", ("M111300", "M113300")),
    IngredientDefinition("Fettarme Milch", ("fettarme milch", "milch 1,5", "milch 1.5", "fettarme h-milch", "h milch 1,5"), "milk lowfat 1%", ("M111200", "M113200")),
    IngredientDefinition("Buttermilch", ("buttermilch", "reine buttermilch"), "buttermilk fluid cultured lowfat", ("M150000",)),
    IngredientDefinition("Sahne", ("sahne", "schlagsahne", "schlagrahm", "rahm", "süße sahne", "kochcreme"), "cream fluid heavy whipping", ("M173800", "M173900")),
    IngredientDefinition("Saure Sahne", ("saure sahne", "sauerrahm", "sour cream", "saure sahne 10 prozent"), "sour cream cultured", ("M172500",)),
    IngredientDefinition("Schmand", ("schmand", "sauerrahm 20 prozent", "schmand 20 prozent"), "sour cream cultured 20 percent", ("M172700",)),
    IngredientDefinition("Crème fraîche", ("crème fraîche", "creme fraiche", "creme fraîche"), "creme fraiche", ("M176800",)),
    IngredientDefinition("Naturjoghurt", ("naturjoghurt", "joghurt natur", "jogurt natur", "joghurt", "yoghurt"), "yogurt plain whole milk", ("M141300",)),
    IngredientDefinition("Magerquark", ("magerquark", "quark mager", "speisequark mager", "quark", "speisequark"), "quark low fat", ("M713100",)),
    IngredientDefinition("Feta", ("feta", "schafskäse", "schafskaese", "salzlakenkäse", "hirtenkäse"), "feta cheese", ("M012200",)),
    IngredientDefinition("Mozzarella", ("mozzarella", "mozzarellakugel", "mozzarella kugel"), "mozzarella cheese whole milk", ("M032100",)),
    IngredientDefinition("Parmesan", ("parmesan", "parmesankäse", "parmesankaese", "geriebener parmesan", "parmesan gerieben", "geriebener parmesankäse", "parmigiano", "parmigiano reggiano"), "parmesan cheese hard", ("M306400",)),
    IngredientDefinition("Butter", ("butter", "süßrahmbutter", "sauerrahmbutter"), "butter salted", ("Q630000",)),
    IngredientDefinition("Ei", ("ei", "eier", "hühnerei", "hühnereier", "vollei"), "egg whole raw fresh", ("E111100",)),
    IngredientDefinition("Eigelb", ("eigelb", "eiergelb", "eidotter", "dotter"), "egg yolk raw fresh", ("E112100",)),
    IngredientDefinition("Eiklar", ("eiklar", "eiweiß", "eiweiss", "eierweiß", "eierweiss"), "egg white raw fresh", ("E113100",)),
    IngredientDefinition("Hähnchenbrust", ("hähnchenbrust", "hähnchenbrustfilet", "hühnerbrust", "huhn brust", "chicken breast"), "chicken breast meat only raw", ("V416100",)),
    IngredientDefinition("Putenbrust", ("putenbrust", "putenbrustfilet", "truthahnbrust"), "turkey breast meat only raw", ("V486100",)),
    IngredientDefinition("Rinderhackfleisch", ("rinderhackfleisch", "rinderhack", "hackfleisch rind", "gehacktes rind"), "ground beef 90% lean raw", ("U010100",)),
    IngredientDefinition("Hackfleisch", ("hackfleisch", "gehacktes", "gemischtes hackfleisch", "hackfleisch gemischt"), "ground beef and pork raw", ("U040100",)),
    IngredientDefinition("Lachs", ("lachs", "lachsfilet", "atlantiklachs"), "salmon atlantic raw", ("T410100", "T410200")),
    IngredientDefinition("Wildlachs", ("wildlachs", "wildlachsfilet"), "salmon sockeye raw", ("T417100",)),
    IngredientDefinition("Seelachs", ("seelachs", "köhler", "koehler", "seelachsfilet"), "pollock raw", ("T207100", "T207200")),
    IngredientDefinition("Alaska-Seelachs", ("alaska seelachs", "alaskaseelachs", "alaska pollack", "alaska-pollack"), "alaska pollock raw", ("T213100",)),
    IngredientDefinition("Kabeljau", ("kabeljau", "dorsch", "kabeljaufilet", "dorschfilet"), "cod pacific raw", ("T204100",)),
    IngredientDefinition("Thunfisch", ("thunfisch", "thunfisch dose", "thunfisch aus der dose", "thunfisch im eigenen saft"), "tuna canned in water drained", ("T121902",)),
    IngredientDefinition("Tofu", ("tofu", "naturtofu", "tofu natur", "sojaquark", "sojakäse"), "tofu raw firm prepared with calcium", ("H861000",)),
    IngredientDefinition("Reis", ("reis", "langkornreis", "basmatireis", "basmati", "jasminreis", "weißer reis"), "rice white long grain regular raw", ("C352000",)),
    IngredientDefinition("Nudeln", ("nudel", "nudeln", "pasta", "spaghetti", "penne", "fusilli", "makkaroni"), "pasta dry unenriched", ("E401000",)),
    IngredientDefinition("Haferflocken", ("haferflocke", "haferflocken", "oats", "porridgeflocken", "zarte haferflocken", "kernige haferflocken"), "oats regular and quick not fortified dry", ("C133000",)),
    IngredientDefinition("Weizenmehl Type 405", ("weizenmehl", "mehl", "weißmehl", "weissmehl", "mehl type 405", "mehl 405", "weizen mehl 405"), "wheat flour white all-purpose unenriched", ("C214100",)),
    IngredientDefinition("Dinkelmehl Type 630", ("dinkelmehl", "dinkel mehl", "dinkelmehl 630", "dinkel mehl 630"), "spelt flour", ("C234000",)),
    IngredientDefinition("Roggenmehl Type 1150", ("roggenmehl", "roggen mehl", "roggenmehl 1150", "roggen mehl 1150"), "rye flour", ("C223300",)),
    IngredientDefinition("Zucker", ("zucker", "haushaltszucker", "kristallzucker", "raffinadezucker"), "sugars granulated", ("S111000",)),
    IngredientDefinition("Salz", ("salz", "speisesalz", "kochsalz", "tafelsalz", "jodsalz"), "salt table", ("R111000",)),
    IngredientDefinition("Senf", ("senf", "tafelsenf", "mittelscharfer senf", "senf mittelscharf", "gelber senf", "yellow mustard"), "mustard prepared yellow", (), ("172234",)),
    IngredientDefinition("Olivenöl", ("olivenöl", "olivenoel", "natives olivenöl", "extra natives olivenöl"), "oil olive salad or cooking", ("Q120000",)),
    IngredientDefinition("Rapsöl", ("rapsöl", "rapsoel", "canolaöl", "canola oil"), "oil canola", ("Q180000",)),
    IngredientDefinition("Sonnenblumenöl", ("sonnenblumenöl", "sonnenblumenoel"), "oil sunflower linoleic", ("Q320000",)),
    IngredientDefinition("Gemüsebrühe", ("gemüsebrühe", "gemüsebruehe", "gemüsefond", "gemüse fond", "brühwürfel gemüse", "brühe gemüse", "vegetable stock", "vegetable broth"), "vegetable broth ready to serve", ("X416243",)),
    IngredientDefinition("Apfel", ("apfel", "äpfel", "aepfel", "tafelapfel"), "apples with skin raw", ("F110100",)),
    IngredientDefinition("Banane", ("banane", "bananen"), "bananas raw", ("F503100",)),
    IngredientDefinition("Zitrone", ("zitrone", "zitronen", "bio zitrone"), "lemons raw without peel", ("F601100",)),
    IngredientDefinition("Fenchel", ("fenchel", "gemüsefenchel", "fenchelknolle", "knollenfenchel"), "fennel bulb raw", ("G430100",)),
    IngredientDefinition("Kohlrabi", ("kohlrabi",), "kohlrabi raw", ("G331100",)),
    IngredientDefinition("Rote Bete", ("rote bete", "rote beete", "rote rübe", "rote ruebe", "rote rüben"), "beets raw", ("G613100",)),
    IngredientDefinition("Rucola", ("rucola", "rauke", "salatrauke"), "arugula raw", ("G130100",)),
    IngredientDefinition("Feldsalat", ("feldsalat", "rapunzel", "nüsslisalat", "vogerlsalat"), "corn salad raw", ("G104100",)),
    IngredientDefinition("Kopfsalat", ("kopfsalat", "buttersalat"), "lettuce butterhead raw", ("G105100",)),
    IngredientDefinition("Eisbergsalat", ("eisbergsalat", "eissalat", "iceberg salat"), "lettuce iceberg raw", ("G103100",)),
    IngredientDefinition("Hokkaidokürbis", ("hokkaido", "hokkaidokürbis", "hokkaido kürbis", "roter kuri"), "squash winter red kuri raw", ("G581000",)),
    IngredientDefinition("Kürbis", ("kürbis", "kuerbis", "speisekürbis", "gartenkürbis"), "pumpkin raw", ("G581100",)),
    IngredientDefinition("Spargel", ("spargel", "weißer spargel", "weisser spargel", "grüner spargel"), "asparagus raw", ("G450100",)),
    IngredientDefinition("Radieschen", ("radieschen", "radies", "radieserl"), "radishes raw", ("G691100",)),
    IngredientDefinition("Rettich", ("rettich", "weißer rettich", "bierrettich"), "radish oriental raw", ("G680100",)),
    IngredientDefinition("Meerrettich", ("meerrettich", "kren"), "horseradish prepared", ("G630100",)),
    IngredientDefinition("Avocado", ("avocado", "avocados"), "avocados raw", ("F502100",)),
    IngredientDefinition("Mango", ("mango", "mangos"), "mangos raw", ("F516100",)),
    IngredientDefinition("Orange", ("orange", "orangen", "apfelsine", "apfelsinen"), "oranges raw", ("F603100",)),
    IngredientDefinition("Birne", ("birne", "birnen", "tafelbirne"), "pears raw", ("F130100",)),
    IngredientDefinition("Erdbeere", ("erdbeere", "erdbeeren"), "strawberries raw", ("F301100",)),
    IngredientDefinition("Blaubeere", ("blaubeere", "blaubeeren", "heidelbeere", "heidelbeeren"), "blueberries raw", ("F304100",)),
    IngredientDefinition("Grüne Bohnen", ("grüne bohnen", "gruene bohnen", "buschbohnen", "brechbohnen", "schnittbohnen"), "green beans raw", ("G710100",)),
    IngredientDefinition("Kichererbsen", ("kichererbse", "kichererbsen", "kichererbsen dose", "kichererbsen aus der dose", "garbanzobohnen"), "chickpeas canned", ("H720902",)),
    IngredientDefinition("Kichererbsen trocken", ("getrocknete kichererbsen", "kichererbsen trocken", "trockene kichererbsen"), "chickpeas mature seeds dry", ("G770400",)),
    IngredientDefinition("Rote Linsen", ("rote linse", "rote linsen"), "lentils red dry", ("H730000",)),
    IngredientDefinition("Linsen", ("linse", "linsen", "braune linsen", "grüne linsen", "berg-linsen", "tellerlinsen"), "lentils mature seeds dry", ("H725100",)),
    IngredientDefinition("Couscous", ("couscous", "kuskus", "hartweizencouscous"), "couscous dry", ("C119200",)),
    IngredientDefinition("Bulgur", ("bulgur", "weizenbulgur", "bulgurweizen"), "bulgur dry", ("C119100",)),
    IngredientDefinition("Petersilie", ("petersilie", "petersilienblatt", "blattpetersilie", "krause petersilie", "glatte petersilie"), "parsley fresh", ("G250100",)),
    IngredientDefinition("Schnittlauch", ("schnittlauch", "schnittlauchhalme"), "chives raw", ("G081100",)),
    IngredientDefinition("Oregano", ("oregano", "wilder majoran", "dost", "getrockneter oregano", "oregano getrocknet"), "spices oregano dried", (), ("171328",)),
)

INGREDIENT_DEFINITIONS = CORE_INGREDIENT_DEFINITIONS + tuple(
    IngredientDefinition(*definition)
    for definition in EXTENDED_INGREDIENT_DEFINITIONS
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
PREFERRED_BLS_INDEX = {}
for definition in INGREDIENT_DEFINITIONS:
    for code in definition.preferred_bls_codes:
        # Spezifische Definitionen stehen vor Oberbegriffen. Ein späterer
        # Oberbegriff wie "Sellerie" darf daher "Staudensellerie" nicht
        # wieder überschreiben.
        PREFERRED_BLS_INDEX.setdefault(code, definition)
PREFERRED_USDA_INDEX = {}
for definition in INGREDIENT_DEFINITIONS:
    for external_id in definition.preferred_usda_ids:
        PREFERRED_USDA_INDEX.setdefault(external_id, definition)


def _fuzzy_definition(normalized):
    if len(normalized) < 5:
        return None
    scores = {}
    for alias, definition in ALIAS_INDEX.items():
        score = SequenceMatcher(None, normalized, alias).ratio()
        if len(alias) > len(normalized):
            score = max(
                score,
                SequenceMatcher(None, normalized, alias[:len(normalized)]).ratio() * 0.96,
            )
        scores[definition] = max(scores.get(definition, 0), score)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] < 0.74:
        return None
    if len(ranked) > 1 and ranked[0][1] - ranked[1][1] < 0.08:
        return None
    return ranked[0][0]


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
    if len(prefix_matches) == 1:
        return next(iter(prefix_matches))
    return _fuzzy_definition(normalized)


def definition_for_canonical(value):
    return CANONICAL_INDEX.get(normalize_alias(value))


def definition_for_product(source, external_id, canonical_name=""):
    if source == "bls":
        matched = PREFERRED_BLS_INDEX.get(str(external_id or "").upper())
        if matched:
            return matched
    if source == "usda":
        matched = PREFERRED_USDA_INDEX.get(str(external_id or ""))
        if matched:
            return matched
    return definition_for_canonical(canonical_name)


def curated_canonical_name(source, external_id):
    definition = definition_for_product(source, external_id)
    return definition.canonical_name if definition else ""


def preferred_bls_codes(value):
    definition = definition_for_query(value)
    return definition.preferred_bls_codes if definition else ()


def preferred_product_keys(value):
    definition = definition_for_query(value)
    if not definition:
        return ()
    return (
        *(("bls", code) for code in definition.preferred_bls_codes),
        *(("usda", external_id) for external_id in definition.preferred_usda_ids),
    )


def display_name_for_query(value):
    definition = definition_for_query(value)
    if not definition:
        return str(value or "").strip()
    if definition.canonical_name in {
        "Chilischote",
        "Rotwein trocken",
        "Weißwein trocken",
        "Sherry trocken",
        "Portwein",
    }:
        return definition.canonical_name
    normalized = normalize_alias(value)
    if normalized == normalize_alias(definition.canonical_name):
        return definition.canonical_name
    for alias in definition.aliases:
        if normalize_alias(alias) == normalized:
            return alias[:1].upper() + alias[1:]
    return definition.canonical_name


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


def aliases_for_product(name, canonical_name="", source="", external_id=""):
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
    for part in re.split(r"\s*/\s*", first_part):
        add(part)
    add(first_part.replace("-", " "))
    add(first_part.replace(" ", ""))
    if "," in without_parentheses:
        left, right = (part.strip() for part in without_parentheses.split(",", 1))
        add(f"{left} {right}")
        add(f"{right} {left}")

    definition = definition_for_product(source, external_id, canonical_name)
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
            product.source,
            product.external_id,
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
            product.source,
            product.external_id,
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
