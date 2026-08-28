"""Erweiterte, redaktionell geprüfte Kochbegriffe.

Jeder Eintrag verweist auf einen konkreten BLS- oder USDA-Datensatz. Die
Synonyme sind Suchbegriffe, keine zusätzlichen Produkte.
"""


# canonical_name, aliases, USDA query, BLS codes, USDA FDC ids
EXTENDED_INGREDIENT_DEFINITIONS = (
    # Brühen und Fonds
    ("Rinderbrühe", ("rinderbrühe", "rinderbruehe", "rinderfond", "rind fond", "beef stock", "beef broth"), "beef broth ready to serve", ("U985200",), ()),
    ("Fleischfond", ("fleischfond", "fleisch fond", "fleischbrühe", "fleischbruehe", "fleischbouillon"), "beef stock ready to serve", ("U981700",), ()),
    ("Hühnerbrühe", ("hühnerbrühe", "huehnerbruehe", "hühnerfond", "huehnerfond", "geflügelfond", "gefluegelfond", "chicken stock", "chicken broth"), "chicken broth ready to serve", ("X411243",), ()),
    ("Fischbrühe", ("fischbrühe", "fischbruehe", "fischfond", "fish stock", "fish broth"), "fish broth", ("X4A1000",), ()),

    # Nüsse, Kerne und Mus
    ("Walnuss", ("walnuss", "walnüsse", "walnuesse", "baumnuss", "baumnüsse", "wallnut", "walnut", "walnuts"), "walnuts raw", ("H120100",), ()),
    ("Haselnuss", ("haselnuss", "haselnüsse", "haselnuesse", "hazelnut", "hazelnuts"), "hazelnuts raw", ("H130100",), ()),
    ("Mandel", ("mandel", "mandeln", "süße mandel", "suesse mandel", "almond", "almonds"), "almonds raw", ("H210100",), ()),
    ("Cashewkern", ("cashew", "cashews", "cashewkern", "cashewkerne", "cashewnuss", "cashewnüsse"), "cashew nuts raw", ("H170100",), ()),
    ("Pekannuss", ("pekannuss", "pekannüsse", "pekannuesse", "pecan", "pecans"), "pecans raw", ("H160100",), ()),
    ("Pistazie", ("pistazie", "pistazien", "pistazienkern", "pistachio", "pistachios"), "pistachio nuts raw", ("H250100",), ()),
    ("Macadamianuss", ("macadamia", "macadamianuss", "macadamianüsse", "macadamianuesse"), "macadamia nuts raw", ("H190100",), ()),
    ("Paranuss", ("paranuss", "paranüsse", "paranuesse", "brazil nut", "brazil nuts"), "brazil nuts raw", ("H180100",), ()),
    ("Pinienkern", ("pinienkern", "pinienkerne", "piniennuss", "pine nut", "pine nuts"), "pine nuts raw", ("H320100",), ()),
    ("Erdnuss", ("erdnuss", "erdnüsse", "erdnuesse", "peanut", "peanuts"), "peanuts roasted", ("H110600",), ()),
    ("Erdnussbutter", ("erdnussbutter", "erdnusscreme", "erdnussmus", "peanut butter"), "peanut butter smooth", ("H880200",), ()),
    ("Sesam", ("sesam", "sesamsamen", "sesamkörner", "sesamkoerner", "sesame"), "sesame seeds whole", ("H420100",), ()),
    ("Tahini", ("tahini", "tahin", "sesammus", "sesampaste"), "sesame butter tahini", ("Q901000",), ()),
    ("Leinsamen", ("leinsamen", "leinsaat", "flachssamen", "flaxseed", "linseed"), "flaxseed", ("H410100",), ()),
    ("Sonnenblumenkerne", ("sonnenblumenkerne", "sonnenblumenkern", "sunflower seeds"), "sunflower seed kernels", ("H430100",), ()),
    ("Kürbiskerne", ("kürbiskerne", "kuerbiskerne", "kürbiskern", "pumpkin seeds", "pepitas"), "pumpkin seeds", ("H310100",), ()),

    # Getreide, Pseudogetreide und Backzutaten
    ("Quinoa", ("quinoa", "inkareis", "reismelde"), "quinoa uncooked", ("C118000",), ()),
    ("Hirse", ("hirse", "goldhirse", "millet"), "millet raw", ("C332000",), ()),
    ("Buchweizen", ("buchweizen", "heidekorn", "buckwheat"), "buckwheat raw", ("C322000",), ()),
    ("Amaranth", ("amaranth", "amaranthkorn", "amaranth grain"), "amaranth grain uncooked", ("C335000",), ()),
    ("Backpulver", ("backpulver", "backtriebmittel", "baking powder"), "baking powder", ("R421100",), ()),
    ("Gelatine", ("gelatine", "speisegelatine", "gelatinepulver"), "gelatin dry powder", ("R468000",), ()),
    ("Trockenhefe", ("trockenhefe", "trockenbackhefe", "backhefe getrocknet", "dry yeast"), "bakers yeast active dry", ("R458000",), ()),
    ("Frischhefe", ("frischhefe", "hefe frisch", "backhefe frisch", "hefewürfel", "hefewuerfel"), "bakers yeast compressed", ("R459000",), ()),
    ("Kakaopulver", ("kakaopulver", "backkakao", "kakao ungesüßt", "kakao ungesuesst", "cocoa powder"), "cocoa powder unsweetened", ("S713000",), ()),
    ("Ahornsirup", ("ahornsirup", "maple syrup"), "maple syrup", ("S151100",), ()),

    # Internationale Gemüse und Hülsenfrüchte
    ("Okra", ("okra", "okraschote", "okraschoten", "ladyfinger"), "okra raw", ("G530100",), ()),
    ("Pak Choi", ("pak choi", "pakchoi", "pak choy", "bok choy", "chinesischer senfkohl"), "pak choi raw", ("G324100",), ()),
    ("Chinakohl", ("chinakohl", "chinesischer kohl", "napa cabbage"), "napa cabbage raw", ("G321100",), ()),
    ("Artischocke", ("artischocke", "artischocken", "artichoke"), "artichokes raw", ("G410100",), ()),
    ("Edamame", ("edamame", "junge sojabohnen", "grüne sojabohnen", "gruene sojabohnen"), "soybeans green raw", ("G750100",), ()),
    ("Sojabohne", ("sojabohne", "sojabohnen", "soybean", "soybeans"), "soybeans mature seeds raw", ("G750400",), ()),
    ("Mungbohne", ("mungbohne", "mungbohnen", "mungo bohne", "mungo beans"), "mung beans raw", ("H770100",), ()),

    # Würzmittel und asiatische Grundzutaten
    ("Basilikum", ("basilikum", "basilikum frisch", "basil", "basil leaves"), "basil fresh", ("G061000",), ()),
    ("Basilikum getrocknet", ("getrockneter basilikum", "basilikum getrocknet", "dried basil"), "basil dried", ("R231000",), ()),
    ("Ingwer", ("ingwer", "ingwerwurzel", "ginger", "frischer ingwer"), "ginger root raw", ("R211200",), ()),
    ("Miso", ("miso", "misopaste", "sojabohnenpaste", "fermentierte sojapaste"), "miso", ("H862200",), ()),
    ("Sojasauce", ("sojasauce", "sojasoße", "sojasosse", "soy sauce"), "soy sauce", ("R143000",), ()),
    ("Sambal Oelek", ("sambal", "sambal oelek", "chilipaste indonesisch"), "sambal oelek", ("R146100",), ()),
    ("Apfelessig", ("apfelessig", "apfel essig", "apple cider vinegar"), "apple cider vinegar", ("R123100",), ()),
    ("Balsamicoessig", ("balsamico", "balsamicoessig", "aceto balsamico", "balsamic vinegar"), "balsamic vinegar", ("R125000",), ()),

    # USDA-Ergänzungen für im BLS nicht vorhandene Grundzutaten
    ("Koriander", ("koriander", "koriandergrün", "koriandergruen", "cilantro", "korianderblätter", "korianderblaetter"), "coriander leaves raw", (), ("169997",)),
    ("Koriandersamen", ("koriandersamen", "korianderkörner", "korianderkoerner", "coriander seeds"), "coriander seed", (), ("170922",)),
    ("Kreuzkümmel", ("kreuzkümmel", "kreuzkuemmel", "cumin", "cumin seed", "jeera"), "cumin seed", (), ("170923",)),
    ("Kurkuma", ("kurkuma", "gelbwurz", "gelbwurzel", "turmeric"), "turmeric ground", (), ("172231",)),
    ("Thymian", ("thymian", "thymian frisch", "fresh thyme"), "thyme fresh", (), ("173470",)),
    ("Thymian getrocknet", ("getrockneter thymian", "thymian getrocknet", "dried thyme"), "thyme dried", (), ("170938",)),
    ("Rosmarin", ("rosmarin", "rosmarin frisch", "fresh rosemary"), "rosemary fresh", (), ("173473",)),
    ("Rosmarin getrocknet", ("getrockneter rosmarin", "rosmarin getrocknet", "dried rosemary"), "rosemary dried", (), ("171333",)),
    ("Majoran", ("majoran", "majoran getrocknet", "marjoram"), "marjoram dried", (), ("170928",)),
    ("Dill", ("dill", "dillspitzen", "dillkraut", "fresh dill"), "dill weed fresh", (), ("172233",)),
    ("Salbei", ("salbei", "salbeiblätter", "salbeiblaetter", "sage"), "sage ground", (), ("170935",)),
    ("Lorbeerblatt", ("lorbeer", "lorbeerblatt", "lorbeerblätter", "lorbeerblaetter", "bay leaf"), "bay leaf", (), ("170917",)),
    ("Muskatnuss", ("muskat", "muskatnuss", "muskatnuß", "nutmeg"), "nutmeg ground", (), ("171326",)),
    ("Gewürznelke", ("nelke", "nelken", "gewürznelke", "gewuerznelke", "clove", "cloves"), "cloves ground", (), ("171321",)),
    ("Zimt", ("zimt", "zimtpulver", "cinnamon"), "cinnamon ground", (), ("171320",)),
    ("Vanilleextrakt", ("vanilleextrakt", "vanille extrakt", "vanilla extract"), "vanilla extract", (), ("173471",)),
    ("Fischsauce", ("fischsauce", "fish sauce", "nam pla", "nuoc mam"), "fish sauce ready to serve", (), ("174531",)),
    ("Kardamom", ("kardamom", "cardamom"), "cardamom", (), ("170919",)),
    ("Safran", ("safran", "saffron"), "saffron", (), ("170934",)),
    ("Schwarzer Pfeffer", ("schwarzer pfeffer", "pfeffer schwarz", "pfeffer", "black pepper"), "black pepper", (), ("170931",)),
    ("Paprikapulver", ("paprikapulver", "paprika edelsüß", "paprika edelsuess", "paprika rosenscharf", "ground paprika"), "paprika ground", (), ("171329",)),
    ("Fenchelsamen", ("fenchelsamen", "fenchelkörner", "fenchelkoerner", "fennel seed"), "fennel seed", (), ("171323",)),
    ("Senfkörner", ("senfkörner", "senfkoerner", "senfsaat", "mustard seed"), "mustard seed ground", (), ("170929",)),
    ("Mohn", ("mohn", "mohnsamen", "blaumohn", "poppy seed"), "poppy seed", (), ("171330",)),
    ("Chiasamen", ("chiasamen", "chia", "chia seeds"), "chia seeds dried", (), ("170554",)),
    ("Wakame", ("wakame", "wakame alge", "wakamealge"), "wakame raw", (), ("170496",)),
    ("Nori", ("nori", "nori alge", "sushi alge", "laver seaweed"), "laver raw", (), ("168458",)),
    ("Jalapeño", ("jalapeño", "jalapeno", "jalapeños", "jalapenos"), "jalapeno raw", (), ("168576",)),
    ("Maisstärke", ("maisstärke", "maisstaerke", "speisestärke mais", "cornstarch"), "cornstarch", (), ("169698",)),
    ("Natron", ("natron", "speisenatron", "baking soda", "natriumbicarbonat"), "baking soda", (), ("175040",)),
)
