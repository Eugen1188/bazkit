import json
from pathlib import Path


DATA_DIR = Path(__file__).parent


def build_names(
    bases,
    prefixes=None,
    suffixes=None
):
    prefixes = prefixes or [""]
    suffixes = suffixes or [""]

    result = []
    seen = set()

    for base in bases:
        for prefix in prefixes:
            for suffix in suffixes:

                parts = [
                    prefix.strip(),
                    base.strip(),
                    suffix.strip()
                ]

                name = " ".join(
                    part
                    for part in parts
                    if part
                )

                normalized = (
                    name.casefold()
                )

                if (
                    not name
                    or
                    normalized in seen
                ):
                    continue

                seen.add(
                    normalized
                )

                result.append(
                    name
                )

    return result


def save_file(
    filename,
    category,
    default_unit,
    bases,
    prefixes=None,
    suffixes=None
):
    names = build_names(
        bases,
        prefixes,
        suffixes
    )

    products = [
        {
            "name": name,
            "category": category,
            "default_unit": default_unit
        }
        for name in names
    ]

    file_path = (
        DATA_DIR
        / filename
    )

    with file_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            products,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"{filename}: "
        f"{len(products)} Produkte"
    )

    return len(products)


total = 0


# =========================================================
# OBST
# =========================================================

total += save_file(
    "fruit.json",
    "Obst",
    "Stück",
    [
        "Apfel",
        "Äpfel",
        "Banane",
        "Bananen",
        "Birne",
        "Birnen",
        "Orange",
        "Orangen",
        "Mandarine",
        "Mandarinen",
        "Clementine",
        "Clementinen",
        "Zitrone",
        "Zitronen",
        "Limette",
        "Limetten",
        "Kiwi",
        "Kiwis",
        "Mango",
        "Ananas",
        "Avocado",
        "Pfirsich",
        "Nektarine",
        "Aprikose",
        "Pflaume",
        "Kirschen",
        "Trauben",
        "Erdbeeren",
        "Himbeeren",
        "Blaubeeren",
        "Heidelbeeren",
        "Brombeeren",
        "Johannisbeeren",
        "Granatapfel",
        "Grapefruit",
        "Wassermelone",
        "Honigmelone",
        "Physalis",
        "Feigen",
        "Datteln"
    ],
    [
        "",
        "Bio",
        "Frisch",
        "Regional"
    ],
    [
        "",
        "lose",
        "Schale",
        "Packung"
    ]
)


# =========================================================
# GEMÜSE
# =========================================================

total += save_file(
    "vegetables.json",
    "Gemüse",
    "g",
    [
        "Tomaten",
        "Cherrytomaten",
        "Cocktailtomaten",
        "Fleischtomaten",
        "Gurke",
        "Salatgurke",
        "Paprika",
        "Rote Paprika",
        "Gelbe Paprika",
        "Grüne Paprika",
        "Karotten",
        "Möhren",
        "Brokkoli",
        "Blumenkohl",
        "Zucchini",
        "Aubergine",
        "Kartoffeln",
        "Süßkartoffeln",
        "Zwiebeln",
        "Rote Zwiebeln",
        "Frühlingszwiebeln",
        "Knoblauch",
        "Lauch",
        "Sellerie",
        "Knollensellerie",
        "Kohlrabi",
        "Rosenkohl",
        "Weißkohl",
        "Rotkohl",
        "Spitzkohl",
        "Wirsing",
        "Spinat",
        "Feldsalat",
        "Eisbergsalat",
        "Kopfsalat",
        "Rucola",
        "Radieschen",
        "Rettich",
        "Mais",
        "Kürbis",
        "Hokkaido Kürbis",
        "Butternut Kürbis",
        "Fenchel",
        "Spargel",
        "Grüner Spargel",
        "Weißer Spargel",
        "Mangold",
        "Pak Choi",
        "Chinakohl"
    ],
    [
        "",
        "Bio",
        "Frisch",
        "Regional"
    ],
    [
        "",
        "lose",
        "Packung",
        "500 g"
    ]
)


# =========================================================
# MILCHPRODUKTE
# =========================================================

total += save_file(
    "dairy.json",
    "Molkereiprodukte",
    "g",
    [
        "Milch",
        "Vollmilch",
        "Frischmilch",
        "H-Milch",
        "Fettarme Milch",
        "Laktosefreie Milch",
        "Buttermilch",
        "Kefir",
        "Naturjoghurt",
        "Griechischer Joghurt",
        "Vanillejoghurt",
        "Erdbeerjoghurt",
        "Kirschjoghurt",
        "Heidelbeerjoghurt",
        "Skyr",
        "Quark",
        "Magerquark",
        "Speisequark",
        "Sahne",
        "Schlagsahne",
        "Saure Sahne",
        "Schmand",
        "Crème fraîche",
        "Butter",
        "Kräuterbutter",
        "Frischkäse",
        "Hüttenkäse",
        "Mascarpone",
        "Ricotta",
        "Trinkjoghurt"
    ],
    [
        "",
        "Bio",
        "Light",
        "Laktosefrei"
    ],
    [
        "",
        "Natur",
        "1,5 %",
        "3,5 %"
    ]
)


# =========================================================
# KÄSE
# =========================================================

total += save_file(
    "cheese.json",
    "Käse",
    "g",
    [
        "Gouda",
        "Junger Gouda",
        "Mittelalter Gouda",
        "Alter Gouda",
        "Emmentaler",
        "Edamer",
        "Mozzarella",
        "Büffelmozzarella",
        "Parmesan",
        "Grana Padano",
        "Cheddar",
        "Feta",
        "Hirtenkäse",
        "Gorgonzola",
        "Camembert",
        "Brie",
        "Bergkäse",
        "Raclettekäse",
        "Halloumi",
        "Maasdamer",
        "Tilsiter",
        "Butterkäse",
        "Ziegenkäse",
        "Schafskäse",
        "Harzer Käse"
    ],
    [
        "",
        "Bio",
        "Light",
        "Premium"
    ],
    [
        "",
        "Scheiben",
        "Geraspelt",
        "Stück"
    ]
)


# =========================================================
# FLEISCH
# =========================================================

total += save_file(
    "meat.json",
    "Fleisch",
    "g",
    [
        "Hähnchenbrust",
        "Hähnchenbrustfilet",
        "Hähnchenfilet",
        "Hähnchenschenkel",
        "Hähnchenflügel",
        "Hähnchenhackfleisch",
        "Hähncheninnenfilet",
        "Putenbrust",
        "Putenfilet",
        "Putensteak",
        "Rinderhackfleisch",
        "Rinderfilet",
        "Rindersteak",
        "Rumpsteak",
        "Roastbeef",
        "Rindergulasch",
        "Rinderrouladen",
        "Rinderhüfte",
        "Rinderbraten",
        "Schweinefilet",
        "Schweineschnitzel",
        "Schweinekotelett",
        "Schweinehackfleisch",
        "Schweinegulasch",
        "Schweinebauch",
        "Schweinenacken",
        "Kalbfleisch",
        "Kalbsschnitzel",
        "Lammfleisch",
        "Lammkotelett"
    ],
    [
        "",
        "Bio",
        "Frisch",
        "Premium"
    ],
    [
        "",
        "natur",
        "mariniert",
        "Familienpackung"
    ]
)


# =========================================================
# FISCH
# =========================================================

total += save_file(
    "fish.json",
    "Fisch",
    "g",
    [
        "Lachs",
        "Lachsfilet",
        "Räucherlachs",
        "Thunfisch",
        "Kabeljau",
        "Kabeljaufilet",
        "Seelachs",
        "Seelachsfilet",
        "Forelle",
        "Dorade",
        "Makrele",
        "Hering",
        "Matjes",
        "Sardinen",
        "Sardellen",
        "Heilbutt",
        "Zander",
        "Rotbarsch",
        "Pangasius",
        "Fischstäbchen"
    ],
    [
        "",
        "Bio",
        "Frisch",
        "MSC"
    ],
    [
        "",
        "Filet",
        "natur",
        "Packung"
    ]
)


# =========================================================
# MEERESFRÜCHTE
# =========================================================

total += save_file(
    "seafood.json",
    "Meeresfrüchte",
    "g",
    [
        "Garnelen",
        "Riesengarnelen",
        "Shrimps",
        "Krabben",
        "Miesmuscheln",
        "Jakobsmuscheln",
        "Venusmuscheln",
        "Tintenfisch",
        "Calamari",
        "Oktopus",
        "Scampi",
        "Hummer",
        "Langusten",
        "Meeresfrüchte Mix",
        "Surimi"
    ],
    [
        "",
        "Frisch",
        "TK",
        "Premium"
    ],
    [
        "",
        "geschält",
        "gekocht",
        "Packung"
    ]
)


# =========================================================
# BACKWAREN
# =========================================================

total += save_file(
    "bakery.json",
    "Backwaren",
    "Stück",
    [
        "Brot",
        "Mischbrot",
        "Vollkornbrot",
        "Roggenbrot",
        "Dinkelbrot",
        "Weizenbrot",
        "Toastbrot",
        "Vollkorntoast",
        "Brötchen",
        "Kaiserbrötchen",
        "Mehrkornbrötchen",
        "Laugenbrötchen",
        "Croissant",
        "Baguette",
        "Ciabatta",
        "Fladenbrot",
        "Pita",
        "Wraps",
        "Tortilla Wraps",
        "Knäckebrot",
        "Zwieback",
        "Bagel",
        "Laugenbrezel",
        "Rosinenbrot",
        "Milchbrötchen",
        "Burger Buns",
        "Hot Dog Brötchen",
        "Pizzateig",
        "Blätterteig",
        "Hefeteig"
    ],
    [
        "",
        "Bio",
        "Frisch",
        "Vollkorn"
    ],
    [
        "",
        "Packung",
        "groß",
        "Mehrpack"
    ]
)


# =========================================================
# NUDELN
# =========================================================

total += save_file(
    "pasta.json",
    "Nudeln",
    "g",
    [
        "Nudeln",
        "Spaghetti",
        "Spaghettini",
        "Penne",
        "Fusilli",
        "Farfalle",
        "Rigatoni",
        "Tagliatelle",
        "Linguine",
        "Lasagneplatten",
        "Makkaroni",
        "Tortellini",
        "Ravioli",
        "Gnocchi",
        "Vollkornnudeln",
        "Dinkelnudeln",
        "Eiernudeln",
        "Reisnudeln",
        "Glasnudeln",
        "Mie-Nudeln",
        "Wok-Nudeln",
        "Udon Nudeln",
        "Soba Nudeln",
        "Suppennudeln"
    ],
    [
        "",
        "Bio",
        "Vollkorn",
        "Glutenfrei"
    ],
    [
        "",
        "500 g",
        "1 kg",
        "Packung"
    ]
)


# =========================================================
# REIS
# =========================================================

total += save_file(
    "rice.json",
    "Reis",
    "g",
    [
        "Reis",
        "Basmati Reis",
        "Jasmin Reis",
        "Langkornreis",
        "Parboiled Reis",
        "Vollkornreis",
        "Risotto Reis",
        "Arborio Reis",
        "Milchreis",
        "Wildreis",
        "Sushi Reis",
        "Naturreis",
        "Duftreis",
        "Schwarzer Reis"
    ],
    [
        "",
        "Bio",
        "Premium",
        "Express"
    ],
    [
        "",
        "500 g",
        "1 kg",
        "Beutel"
    ]
)


# =========================================================
# GETREIDE
# =========================================================

total += save_file(
    "grains.json",
    "Getreide",
    "g",
    [
        "Quinoa",
        "Couscous",
        "Bulgur",
        "Hirse",
        "Gerste",
        "Dinkel",
        "Weizen",
        "Roggen",
        "Hafer",
        "Buchweizen",
        "Amaranth",
        "Polenta",
        "Grieß",
        "Hartweizengrieß",
        "Weizenkleie"
    ],
    [
        "",
        "Bio",
        "Vollkorn",
        "Fein"
    ],
    [
        "",
        "500 g",
        "1 kg",
        "Packung"
    ]
)


# =========================================================
# MEHL
# =========================================================

total += save_file(
    "flour.json",
    "Mehl",
    "kg",
    [
        "Weizenmehl",
        "Weizenmehl Type 405",
        "Weizenmehl Type 550",
        "Dinkelmehl",
        "Dinkelmehl Type 630",
        "Vollkornmehl",
        "Roggenmehl",
        "Maismehl",
        "Reismehl",
        "Mandelmehl"
    ],
    [
        "",
        "Bio",
        "Glutenfrei",
        "Premium"
    ],
    [
        "",
        "500 g",
        "1 kg",
        "Packung"
    ]
)


# =========================================================
# HÜLSENFRÜCHTE
# =========================================================

total += save_file(
    "beans.json",
    "Hülsenfrüchte",
    "g",
    [
        "Kidneybohnen",
        "Weiße Bohnen",
        "Schwarze Bohnen",
        "Pintobohnen",
        "Kichererbsen",
        "Linsen",
        "Rote Linsen",
        "Grüne Linsen",
        "Braune Linsen",
        "Belugalinsen",
        "Erbsen",
        "Gelbe Erbsen",
        "Sojabohnen",
        "Edamame",
        "Mungbohnen"
    ],
    [
        "",
        "Bio",
        "Getrocknet",
        "Vorgekocht"
    ],
    [
        "",
        "500 g",
        "Dose",
        "Packung"
    ]
)


# =========================================================
# KONSERVEN
# =========================================================

total += save_file(
    "canned_food.json",
    "Konserven",
    "Dose",
    [
        "Mais",
        "Erbsen",
        "Möhren",
        "Kidneybohnen",
        "Weiße Bohnen",
        "Kichererbsen",
        "Tomaten",
        "Gehackte Tomaten",
        "Geschälte Tomaten",
        "Tomatenmark",
        "Thunfisch",
        "Sardinen",
        "Ananas",
        "Pfirsiche",
        "Mandarinen",
        "Champignons",
        "Sauerkraut",
        "Rotkohl",
        "Linsen",
        "Ravioli"
    ],
    [
        "",
        "Bio",
        "Fein",
        "Premium"
    ],
    [
        "",
        "Dose",
        "Glas",
        "Vorratspackung"
    ]
)


# =========================================================
# FRÜHSTÜCK
# =========================================================

total += save_file(
    "breakfast.json",
    "Frühstück",
    "Packung",
    [
        "Müsli",
        "Früchtemüsli",
        "Schokomüsli",
        "Knuspermüsli",
        "Cornflakes",
        "Haferflocken",
        "Zarte Haferflocken",
        "Kernige Haferflocken",
        "Granola",
        "Porridge",
        "Honig",
        "Marmelade",
        "Nuss-Nougat-Creme",
        "Erdnussbutter",
        "Ahornsirup",
        "Frühstückskekse",
        "Reiswaffeln",
        "Knäckebrot",
        "Protein Müsli",
        "Bircher Müsli"
    ],
    [
        "",
        "Bio",
        "Protein",
        "Zuckerreduziert"
    ],
    [
        "",
        "500 g",
        "Familienpackung",
        "Packung"
    ]
)


# =========================================================
# CEREALIEN
# =========================================================

total += save_file(
    "cereals.json",
    "Cerealien",
    "g",
    [
        "Cornflakes",
        "Schoko Cornflakes",
        "Honig Cornflakes",
        "Müsli",
        "Knuspermüsli",
        "Granola",
        "Haferflocken",
        "Dinkelflocken",
        "Reisflakes",
        "Schokokissen",
        "Frühstücksringe",
        "Protein Cerealien",
        "Kinder Cerealien",
        "Vollkornflakes",
        "Porridge"
    ],
    [
        "",
        "Bio",
        "Vollkorn",
        "Zuckerreduziert"
    ],
    [
        "",
        "375 g",
        "500 g",
        "Familienpackung"
    ]
)


# =========================================================
# GETRÄNKE
# =========================================================

total += save_file(
    "drinks.json",
    "Getränke",
    "Liter",
    [
        "Mineralwasser",
        "Stilles Wasser",
        "Sprudelwasser",
        "Apfelsaft",
        "Orangensaft",
        "Multivitaminsaft",
        "Traubensaft",
        "Tomatensaft",
        "Kirschsaft",
        "Ananassaft",
        "Cola",
        "Cola Zero",
        "Cola Light",
        "Limonade",
        "Orangenlimonade",
        "Zitronenlimonade",
        "Eistee Pfirsich",
        "Eistee Zitrone",
        "Energy Drink",
        "Tonic Water",
        "Ginger Ale",
        "Bitter Lemon",
        "Apfelschorle",
        "Rhabarberschorle",
        "Kokoswasser",
        "Smoothie",
        "Protein Drink",
        "Isotonisches Getränk"
    ],
    [
        "",
        "Bio",
        "Zero",
        "Light",
        "Premium"
    ],
    [
        "",
        "0,5 l",
        "1 l",
        "1,5 l",
        "Mehrpack"
    ]
)


# =========================================================
# SONSTIGE GETRÄNKE
# =========================================================

total += save_file(
    "beverages.json",
    "Getränke",
    "Liter",
    [
        "Fruchtsaftgetränk",
        "Nektar",
        "Schorle",
        "Vitaminwasser",
        "Elektrolytgetränk",
        "Sportgetränk",
        "Malzgetränk",
        "Ingwershot",
        "Kurkuma Shot",
        "Aloe Vera Getränk",
        "Kombucha",
        "Mate Getränk",
        "Kakao Getränk",
        "Milchdrink",
        "Haferdrink"
    ],
    [
        "",
        "Bio",
        "Zero",
        "Natur"
    ],
    [
        "",
        "0,33 l",
        "0,5 l",
        "1 l"
    ]
)


# =========================================================
# KAFFEE
# =========================================================

total += save_file(
    "coffee.json",
    "Kaffee",
    "g",
    [
        "Kaffeebohnen",
        "Espressobohnen",
        "Filterkaffee",
        "Instantkaffee",
        "Kaffeepads",
        "Kaffeekapseln",
        "Espresso",
        "Caffè Crema",
        "Arabica Kaffee",
        "Robusta Kaffee",
        "Entkoffeinierter Kaffee",
        "Cold Brew",
        "Cappuccino Pulver",
        "Latte Macchiato Pulver",
        "Eiskaffee"
    ],
    [
        "",
        "Bio",
        "Premium",
        "Mild",
        "Kräftig"
    ],
    [
        "",
        "250 g",
        "500 g",
        "1 kg"
    ]
)


# =========================================================
# TEE
# =========================================================

total += save_file(
    "tea.json",
    "Tee",
    "Packung",
    [
        "Schwarzer Tee",
        "Grüner Tee",
        "Weißer Tee",
        "Kamillentee",
        "Pfefferminztee",
        "Früchtetee",
        "Kräutertee",
        "Fencheltee",
        "Ingwertee",
        "Hagebuttentee",
        "Rooibostee",
        "Chai Tee",
        "Matcha Tee",
        "Salbeitee",
        "Brennnesseltee",
        "Zitronentee",
        "Himbeertee",
        "Earl Grey",
        "Darjeeling",
        "Assam Tee"
    ],
    [
        "",
        "Bio",
        "Premium",
        "Lose",
        "Teebeutel"
    ],
    [
        "",
        "20 Beutel",
        "40 Beutel",
        "Packung"
    ]
)


# =========================================================
# SÜSSWAREN
# =========================================================

total += save_file(
    "sweets.json",
    "Süßwaren",
    "Packung",
    [
        "Nutella",
        "Schokolade",
        "Vollmilchschokolade",
        "Zartbitterschokolade",
        "Weiße Schokolade",
        "Haselnussschokolade",
        "Mandelschokolade",
        "Schokoriegel",
        "Karamellriegel",
        "Gummibärchen",
        "Fruchtgummi",
        "Bonbons",
        "Kaubonbons",
        "Kekse",
        "Butterkekse",
        "Schokokekse",
        "Waffeln",
        "Pralinen",
        "Marshmallows",
        "Lakritz",
        "Schoko Bons",
        "Nougat",
        "Marzipan",
        "Schokodrops",
        "Dragées",
        "Toffee",
        "Karamellbonbons",
        "Lutscher"
    ],
    [
        "",
        "Mini",
        "XXL",
        "Premium",
        "Zuckerfrei"
    ],
    [
        "",
        "Packung",
        "Familienpackung",
        "Vorratspackung",
        "200 g"
    ]
)


# =========================================================
# SNACKS
# =========================================================

total += save_file(
    "snacks.json",
    "Snacks",
    "Packung",
    [
        "Chips",
        "Paprika Chips",
        "Salz Chips",
        "Käse Chips",
        "Tortilla Chips",
        "Nachos",
        "Salzstangen",
        "Cracker",
        "Popcorn",
        "Mikrowellen Popcorn",
        "Nussmix",
        "Studentenfutter",
        "Erdnüsse",
        "Cashews",
        "Mandeln",
        "Pistazien",
        "Reiswaffeln",
        "Maiswaffeln",
        "Proteinriegel",
        "Müsliriegel",
        "Fruchtriegel",
        "Knäckebrot",
        "Mini Brezeln",
        "Snack Mix",
        "Kartoffelsticks",
        "Taco Chips",
        "Linsen Chips",
        "Kichererbsen Chips"
    ],
    [
        "",
        "Bio",
        "XXL",
        "Protein",
        "Light"
    ],
    [
        "",
        "Packung",
        "Familienpackung",
        "200 g",
        "300 g"
    ]
)


# =========================================================
# TIEFKÜHL
# =========================================================

total += save_file(
    "frozen.json",
    "Tiefkühl",
    "Packung",
    [
        "Tiefkühlpizza",
        "Pizza Margherita",
        "Pizza Salami",
        "Pizza Schinken",
        "Pizza Funghi",
        "Pommes",
        "Wedges",
        "Kroketten",
        "TK Gemüse",
        "TK Brokkoli",
        "TK Spinat",
        "TK Erbsen",
        "TK Beeren",
        "TK Erdbeeren",
        "TK Himbeeren",
        "Fischstäbchen",
        "Chicken Nuggets",
        "Hähnchen Wings",
        "Schnitzel",
        "Lasagne",
        "Nudelpfanne",
        "Reispfanne",
        "Gemüsepfanne",
        "Eiscreme",
        "Vanilleeis",
        "Schokoladeneis",
        "Sorbet",
        "Tiefkühlbrötchen"
    ],
    [
        "",
        "Bio",
        "Premium",
        "Familien"
    ],
    [
        "",
        "Packung",
        "500 g",
        "1 kg"
    ]
)


# =========================================================
# GEWÜRZE
# =========================================================

total += save_file(
    "spices.json",
    "Gewürze",
    "g",
    [
        "Salz",
        "Meersalz",
        "Pfeffer",
        "Schwarzer Pfeffer",
        "Weißer Pfeffer",
        "Paprikapulver",
        "Paprika edelsüß",
        "Paprika rosenscharf",
        "Currypulver",
        "Chilipulver",
        "Chiliflocken",
        "Cayennepfeffer",
        "Kurkuma",
        "Kreuzkümmel",
        "Koriander",
        "Zimt",
        "Muskat",
        "Nelken",
        "Piment",
        "Ingwer",
        "Knoblauchpulver",
        "Zwiebelpulver",
        "Oregano",
        "Basilikum",
        "Thymian",
        "Rosmarin",
        "Majoram",
        "Dill",
        "Petersilie",
        "Lorbeerblätter",
        "Fenchelsamen",
        "Kardamom",
        "Anis",
        "Sternanis",
        "Vanille",
        "Safran",
        "Garam Masala",
        "Ras el Hanout"
    ],
    [
        "",
        "Bio",
        "Gemahlen",
        "Ganz"
    ],
    [
        "",
        "Dose",
        "Beutel",
        "Nachfüllpack"
    ]
)


# =========================================================
# KRÄUTER
# =========================================================

total += save_file(
    "herbs.json",
    "Kräuter",
    "Bund",
    [
        "Petersilie",
        "Glatte Petersilie",
        "Krause Petersilie",
        "Basilikum",
        "Dill",
        "Schnittlauch",
        "Koriander",
        "Rosmarin",
        "Thymian",
        "Salbei",
        "Minze",
        "Oregano",
        "Majoram",
        "Estragon",
        "Zitronenmelisse"
    ],
    [
        "",
        "Bio",
        "Frisch",
        "Getrocknet"
    ],
    [
        "",
        "Bund",
        "Topf",
        "Packung"
    ]
)


# =========================================================
# SAUCEN
# =========================================================

total += save_file(
    "sauces.json",
    "Soßen",
    "Flasche",
    [
        "Tomatensauce",
        "Pastasauce",
        "Bolognese Sauce",
        "Arrabbiata Sauce",
        "BBQ Sauce",
        "Chilisauce",
        "Sweet Chili Sauce",
        "Knoblauchsauce",
        "Currysauce",
        "Cocktailsauce",
        "Remoulade",
        "Burger Sauce",
        "Teriyaki Sauce",
        "Sojasauce",
        "Fischsauce",
        "Austernsauce",
        "Sriracha",
        "Salsa",
        "Pesto",
        "Pesto Rosso",
        "Pesto Verde",
        "Hollandaise",
        "Bratensauce",
        "Rahmsauce",
        "Jägersauce",
        "Tzatziki",
        "Aioli",
        "Salatdressing"
    ],
    [
        "",
        "Bio",
        "Scharf",
        "Light"
    ],
    [
        "",
        "Flasche",
        "Glas",
        "XXL"
    ]
)


# =========================================================
# WÜRZMITTEL
# =========================================================

total += save_file(
    "condiments.json",
    "Würzmittel",
    "Flasche",
    [
        "Ketchup",
        "Tomatenketchup",
        "Curry Ketchup",
        "Mayonnaise",
        "Senf",
        "Mittelscharfer Senf",
        "Dijon Senf",
        "Sojasauce",
        "Worcestersauce",
        "Tabasco",
        "Meerrettich",
        "Wasabi",
        "Maggi Würze",
        "Essig Essenz",
        "Sambal Oelek"
    ],
    [
        "",
        "Bio",
        "Light",
        "Scharf"
    ],
    [
        "",
        "Flasche",
        "Glas",
        "Tube"
    ]
)


# =========================================================
# ÖLE
# =========================================================

total += save_file(
    "oils.json",
    "Öle",
    "Liter",
    [
        "Olivenöl",
        "Natives Olivenöl",
        "Rapsöl",
        "Sonnenblumenöl",
        "Kokosöl",
        "Sesamöl",
        "Walnussöl",
        "Leinöl",
        "Erdnussöl",
        "Avocadoöl",
        "Traubenkernöl",
        "Kürbiskernöl",
        "Distelöl",
        "Maiskeimöl",
        "Bratöl"
    ],
    [
        "",
        "Bio",
        "Nativ",
        "Kaltgepresst"
    ],
    [
        "",
        "250 ml",
        "500 ml",
        "1 l"
    ]
)


# =========================================================
# ESSIG
# =========================================================

total += save_file(
    "vinegar.json",
    "Essig",
    "Liter",
    [
        "Apfelessig",
        "Balsamico",
        "Weißer Balsamico",
        "Weißweinessig",
        "Rotweinessig",
        "Kräuteressig",
        "Reisessig",
        "Branntweinessig",
        "Himbeeressig",
        "Sherryessig"
    ],
    [
        "",
        "Bio",
        "Premium",
        "Naturtrüb"
    ],
    [
        "",
        "250 ml",
        "500 ml",
        "1 l"
    ]
)


# =========================================================
# NÜSSE
# =========================================================

total += save_file(
    "nuts.json",
    "Nüsse",
    "g",
    [
        "Mandeln",
        "Walnüsse",
        "Haselnüsse",
        "Cashews",
        "Pistazien",
        "Erdnüsse",
        "Macadamia",
        "Paranüsse",
        "Pekannüsse",
        "Pinienkerne",
        "Nussmix",
        "Studentenfutter",
        "Kürbiskerne",
        "Sonnenblumenkerne",
        "Chiasamen"
    ],
    [
        "",
        "Bio",
        "Geröstet",
        "Gesalzen"
    ],
    [
        "",
        "200 g",
        "500 g",
        "Packung"
    ]
)


# =========================================================
# PILZE
# =========================================================

total += save_file(
    "mushrooms.json",
    "Pilze",
    "g",
    [
        "Champignons",
        "Braune Champignons",
        "Weiße Champignons",
        "Pfifferlinge",
        "Steinpilze",
        "Austernpilze",
        "Shiitake",
        "Kräuterseitlinge",
        "Morcheln",
        "Pilzmischung"
    ],
    [
        "",
        "Bio",
        "Frisch",
        "Getrocknet"
    ],
    [
        "",
        "200 g",
        "500 g",
        "Packung"
    ]
)


# =========================================================
# EIER
# =========================================================

total += save_file(
    "eggs.json",
    "Eier",
    "Stück",
    [
        "Eier",
        "Hühnereier",
        "Bio Eier",
        "Freiland Eier",
        "Bodenhaltung Eier",
        "Wachteleier",
        "Braune Eier",
        "Weiße Eier",
        "Frische Eier",
        "Frühstückseier"
    ],
    [
        "",
        "Bio",
        "Größe M",
        "Größe L"
    ],
    [
        "",
        "6 Stück",
        "10 Stück",
        "12 Stück"
    ]
)


# =========================================================
# SUPPEN
# =========================================================

total += save_file(
    "soups.json",
    "Suppen",
    "Dose",
    [
        "Tomatensuppe",
        "Hühnersuppe",
        "Gemüsesuppe",
        "Kartoffelsuppe",
        "Linsensuppe",
        "Erbsensuppe",
        "Gulaschsuppe",
        "Kürbissuppe",
        "Brokkolisuppe",
        "Pilzsuppe",
        "Nudelsuppe",
        "Rindfleischsuppe",
        "Minestrone",
        "Zwiebelsuppe",
        "Käsesuppe",
        "Karottensuppe",
        "Spargelsuppe",
        "Thai Suppe",
        "Kokossuppe",
        "Chili Suppe"
    ],
    [
        "",
        "Bio",
        "Cremig",
        "Herzhaft"
    ],
    [
        "",
        "Dose",
        "Glas",
        "Beutel"
    ]
)


# =========================================================
# DESSERTS
# =========================================================

total += save_file(
    "desserts.json",
    "Desserts",
    "Packung",
    [
        "Pudding",
        "Vanillepudding",
        "Schokopudding",
        "Karamellpudding",
        "Tiramisu",
        "Milchreis",
        "Grießpudding",
        "Mousse au Chocolat",
        "Panna Cotta",
        "Rote Grütze",
        "Vanillesauce",
        "Schokosauce",
        "Fruchtquark",
        "Dessertcreme",
        "Wackelpudding",
        "Cheesecake Dessert",
        "Profiteroles",
        "Schokodessert",
        "Vanilledessert",
        "Joghurt Dessert"
    ],
    [
        "",
        "Bio",
        "Light",
        "Premium"
    ],
    [
        "",
        "Becher",
        "2er Pack",
        "4er Pack"
    ]
)


# =========================================================
# MARMELADE / AUFSTRICHE
# =========================================================

total += save_file(
    "jams.json",
    "Brotaufstriche",
    "Glas",
    [
        "Erdbeermarmelade",
        "Himbeermarmelade",
        "Aprikosenmarmelade",
        "Kirschmarmelade",
        "Pflaumenmus",
        "Orangenmarmelade",
        "Waldfruchtmarmelade",
        "Honig",
        "Blütenhonig",
        "Waldhonig",
        "Nutella",
        "Nuss-Nougat-Creme"
    ],
    [
        "",
        "Bio",
        "Extra",
        "Zuckerreduziert"
    ],
    [
        "",
        "Glas",
        "250 g",
        "500 g"
    ]
)


# =========================================================
# VEGAN
# =========================================================

total += save_file(
    "vegan.json",
    "Vegan",
    "Packung",
    [
        "Tofu",
        "Naturtofu",
        "Räuchertofu",
        "Tempeh",
        "Seitan",
        "Veganes Hack",
        "Vegane Burger",
        "Vegane Frikadellen",
        "Vegane Nuggets",
        "Vegane Wurst",
        "Vegane Salami",
        "Veganer Käse",
        "Veganer Frischkäse",
        "Vegane Mayonnaise",
        "Haferdrink",
        "Sojadrink",
        "Mandeldrink",
        "Kokosdrink",
        "Erbsendrink",
        "Vegane Sahne",
        "Vegane Butter",
        "Vegane Pizza",
        "Veganes Eis",
        "Vegane Schokolade"
    ],
    [
        "",
        "Bio",
        "Protein",
        "Premium",
        "Natur"
    ],
    [
        "",
        "Packung",
        "200 g",
        "400 g"
    ]
)


# =========================================================
# VEGETARISCH
# =========================================================

total += save_file(
    "vegetarian.json",
    "Vegetarisch",
    "Packung",
    [
        "Vegetarische Frikadellen",
        "Vegetarische Nuggets",
        "Vegetarische Wurst",
        "Vegetarische Salami",
        "Vegetarischer Burger",
        "Vegetarisches Hack",
        "Falafel",
        "Halloumi",
        "Gemüseburger",
        "Käse Schnitzel",
        "Gemüse Schnitzel",
        "Spinat Tasche",
        "Gemüse Nuggets",
        "Vegetarische Pizza",
        "Vegetarische Lasagne",
        "Käsespätzle",
        "Gemüsepfanne",
        "Kartoffeltaschen",
        "Mozzarella Sticks",
        "Veggie Bällchen"
    ],
    [
        "",
        "Bio",
        "Protein",
        "Premium",
        "Frisch"
    ],
    [
        "",
        "Packung",
        "200 g",
        "400 g"
    ]
)


# =========================================================
# DROGERIE
# =========================================================

total += save_file(
    "drugstore.json",
    "Drogerie",
    "Stück",
    [
        "Shampoo",
        "Anti-Schuppen Shampoo",
        "Duschgel",
        "Duschcreme",
        "Zahnpasta",
        "Zahnbürste",
        "Mundspülung",
        "Zahnseide",
        "Deodorant",
        "Deospray",
        "Deoroller",
        "Rasierschaum",
        "Rasiergel",
        "Rasierer",
        "Rasierklingen",
        "Handseife",
        "Flüssigseife",
        "Bodylotion",
        "Handcreme",
        "Gesichtscreme",
        "Sonnencreme",
        "Lippenpflege",
        "Haarspray",
        "Haargel",
        "Haarwachs",
        "Conditioner",
        "Haarkur",
        "Wattestäbchen",
        "Wattepads",
        "Taschentücher",
        "Feuchttücher",
        "Tampons",
        "Binden",
        "Slipeinlagen",
        "Damenrasierer",
        "Herrenrasierer"
    ],
    [
        "",
        "Sensitive",
        "Premium",
        "Natur",
        "Extra"
    ],
    [
        "",
        "klein",
        "groß",
        "Vorratspackung"
    ]
)


# =========================================================
# REINIGUNG
# =========================================================

total += save_file(
    "cleaning.json",
    "Reinigung",
    "Flasche",
    [
        "Spülmittel",
        "Spülmaschinen Tabs",
        "Klarspüler",
        "Spülmaschinensalz",
        "Waschmittel",
        "Color Waschmittel",
        "Vollwaschmittel",
        "Feinwaschmittel",
        "Weichspüler",
        "Fleckentferner",
        "Allzweckreiniger",
        "Glasreiniger",
        "Badreiniger",
        "WC-Reiniger",
        "Küchenreiniger",
        "Backofenreiniger",
        "Entkalker",
        "Rohrreiniger",
        "Bodenreiniger",
        "Parkettreiniger",
        "Teppichreiniger",
        "Desinfektionsmittel",
        "Hygienereiniger",
        "Scheuermilch",
        "Möbelpolitur",
        "Edelstahlreiniger",
        "Schimmelentferner",
        "Waschmaschinenreiniger"
    ],
    [
        "",
        "Eco",
        "Sensitive",
        "Extra Stark",
        "Konzentrat"
    ],
    [
        "",
        "Flasche",
        "Nachfüllpack",
        "Vorratspackung"
    ]
)


# =========================================================
# HAUSHALT
# =========================================================

total += save_file(
    "household.json",
    "Haushalt",
    "Packung",
    [
        "Küchenrolle",
        "Toilettenpapier",
        "Taschentücher",
        "Müllbeutel",
        "Bio Müllbeutel",
        "Alufolie",
        "Frischhaltefolie",
        "Backpapier",
        "Gefrierbeutel",
        "Frischhaltebeutel",
        "Schwämme",
        "Topfschwämme",
        "Spültücher",
        "Mikrofasertücher",
        "Gummihandschuhe",
        "Einweghandschuhe",
        "Batterien",
        "Teelichter",
        "Kerzen",
        "Streichhölzer",
        "Feuerzeug",
        "Kaffeefilter",
        "Staubsaugerbeutel",
        "Wäscheklammern",
        "Papierservietten",
        "Pappteller",
        "Pappbecher",
        "Trinkhalme"
    ],
    [
        "",
        "Eco",
        "Premium",
        "XXL",
        "Extra"
    ],
    [
        "",
        "Packung",
        "Mehrpack",
        "Vorratspackung"
    ]
)


# =========================================================
# BABY
# =========================================================

total += save_file(
    "baby.json",
    "Baby",
    "Packung",
    [
        "Babybrei",
        "Milchbrei",
        "Getreidebrei",
        "Obstbrei",
        "Gemüsebrei",
        "Babygläschen",
        "Babynahrung",
        "Babymilch",
        "Pre Nahrung",
        "Folgemilch",
        "Kindermilch",
        "Windeln",
        "Pants",
        "Feuchttücher",
        "Babyshampoo",
        "Babybad",
        "Babyöl",
        "Babycreme",
        "Wundschutzcreme",
        "Schnuller",
        "Babyflasche",
        "Trinksauger",
        "Lätzchen",
        "Baby Snacks"
    ],
    [
        "",
        "Bio",
        "Sensitive",
        "Premium",
        "Extra"
    ],
    [
        "",
        "Packung",
        "Vorratspackung",
        "Mehrpack"
    ]
)


# =========================================================
# TIERBEDARF
# =========================================================

total += save_file(
    "pet_food.json",
    "Tierbedarf",
    "Packung",
    [
        "Hundefutter",
        "Hunde Trockenfutter",
        "Hunde Nassfutter",
        "Welpenfutter",
        "Hunde Snacks",
        "Hundeknochen",
        "Katzenfutter",
        "Katzen Trockenfutter",
        "Katzen Nassfutter",
        "Kittenfutter",
        "Katzensnacks",
        "Katzenstreu",
        "Klumpstreu",
        "Vogelfutter",
        "Wellensittichfutter",
        "Nagerfutter",
        "Kaninchenfutter",
        "Meerschweinchenfutter",
        "Fischfutter",
        "Aquarienfutter",
        "Hunde Shampoo",
        "Katzen Shampoo",
        "Kotbeutel",
        "Tierstreu"
    ],
    [
        "",
        "Premium",
        "Sensitive",
        "Adult",
        "Junior"
    ],
    [
        "",
        "Packung",
        "1 kg",
        "Vorratspackung"
    ]
)


print()
print(
    "=================================="
)

print(
    f"Insgesamt erzeugt: {total} Einträge"
)

print(
    "=================================="
)