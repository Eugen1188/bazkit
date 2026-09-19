"""Kuratierte Startinhalte für die klar gekennzeichneten Bazkit-Profile."""


EDITORIAL_PROFILES = (
    {
        "username": "bazkit-alltagskueche",
        "email": "alltagskueche@redaktion.bazkit.local",
        "display_name": "Bazkit Alltagsküche",
    },
    {
        "username": "bazkit-veggie",
        "email": "veggie@redaktion.bazkit.local",
        "display_name": "Bazkit Veggie",
    },
    {
        "username": "bazkit-weltkueche",
        "email": "weltkueche@redaktion.bazkit.local",
        "display_name": "Bazkit Weltküche",
    },
    {
        "username": "bazkit-backstube",
        "email": "backstube@redaktion.bazkit.local",
        "display_name": "Bazkit Backstube",
    },
)


EDITORIAL_RECIPES = (
    {
        "profile": "bazkit-alltagskueche",
        "name": "Cremige Kartoffel-Möhren-Suppe",
        "description": "Eine unkomplizierte, wärmende Gemüsesuppe für den Feierabend.",
        "servings": 4,
        "preparation_time": 40,
        "category": "dinner",
        "instructions": (
            "1. Kartoffeln, Möhren und Zwiebel schälen und grob würfeln.\n"
            "2. Rapsöl in einem großen Topf erhitzen, Zwiebel und Knoblauch darin glasig dünsten.\n"
            "3. Kartoffeln und Möhren zugeben, knapp mit Wasser bedecken und 25 Minuten weich kochen.\n"
            "4. Die Suppe fein pürieren, Sahne einrühren und mit Salz abschmecken."
        ),
        "notes": "Mit frischen Kräutern oder gerösteten Brotwürfeln servieren.",
        "ingredients": (
            ("Kartoffel", "600", "g", "geschält"),
            ("Karotte", "300", "g", "geschält"),
            ("Zwiebel", "120", "g", "grob gewürfelt"),
            ("Knoblauch", "10", "g", "fein gehackt"),
            ("Rapsöl", "15", "ml", ""),
            ("Sahne", "150", "ml", ""),
            ("Salz", "5", "g", "nach Geschmack"),
        ),
    },
    {
        "profile": "bazkit-alltagskueche",
        "name": "One-Pot-Tomatenpasta mit Spinat",
        "description": "Cremige Tomatenpasta aus nur einem Topf – schnell und familientauglich.",
        "servings": 4,
        "preparation_time": 30,
        "category": "dinner",
        "instructions": (
            "1. Zwiebel und Knoblauch fein hacken und im Olivenöl kurz anschwitzen.\n"
            "2. Dosentomaten, Nudeln und 500 ml Wasser zugeben und aufkochen.\n"
            "3. Unter regelmäßigem Rühren 12 bis 15 Minuten köcheln, bis die Nudeln gar sind.\n"
            "4. Spinat unterheben, zusammenfallen lassen und mit Parmesan servieren."
        ),
        "notes": "Falls die Pasta zu trocken wird, schluckweise Wasser ergänzen.",
        "ingredients": (
            ("Nudeln", "320", "g", "kurze Nudelform"),
            ("Dosentomaten", "500", "g", "gehackt"),
            ("Zwiebel", "100", "g", "fein gewürfelt"),
            ("Knoblauch", "10", "g", "fein gehackt"),
            ("Spinat", "150", "g", "frisch oder tiefgekühlt"),
            ("Parmesan", "60", "g", "frisch gerieben"),
            ("Olivenöl", "15", "ml", ""),
        ),
    },
    {
        "profile": "bazkit-alltagskueche",
        "name": "Hähnchen-Gemüse-Blech",
        "description": "Saftiges Hähnchen und buntes Ofengemüse mit wenig Abwasch.",
        "servings": 4,
        "preparation_time": 50,
        "category": "dinner",
        "instructions": (
            "1. Backofen auf 210 °C Ober-/Unterhitze vorheizen.\n"
            "2. Kartoffeln klein schneiden und mit Olivenöl auf einem Blech verteilen. 15 Minuten vorgaren.\n"
            "3. Hähnchen, Brokkoli und Paprika ergänzen, salzen und alles gut vermengen.\n"
            "4. Weitere 25 Minuten backen, bis das Hähnchen durchgegart und das Gemüse gebräunt ist."
        ),
        "notes": "Für gleichmäßiges Garen die Kartoffelstücke nicht zu groß schneiden.",
        "ingredients": (
            ("Hähnchenbrust", "600", "g", "in mundgerechten Stücken"),
            ("Kartoffel", "700", "g", "in kleinen Spalten"),
            ("Brokkoli", "350", "g", "in Röschen"),
            ("Paprika rot", "250", "g", "in Streifen"),
            ("Olivenöl", "30", "ml", ""),
            ("Salz", "5", "g", "nach Geschmack"),
        ),
    },
    {
        "profile": "bazkit-veggie",
        "name": "Rote-Linsen-Dal mit Spinat",
        "description": "Würzig, cremig und in einer halben Stunde auf dem Tisch.",
        "servings": 4,
        "preparation_time": 35,
        "category": "dinner",
        "instructions": (
            "1. Zwiebel und Knoblauch fein hacken und im Rapsöl glasig dünsten.\n"
            "2. Linsen, Dosentomaten und Kokosmilch zugeben und 20 Minuten sanft köcheln.\n"
            "3. Zwischendurch umrühren und bei Bedarf etwas Wasser ergänzen.\n"
            "4. Spinat unterheben, fünf Minuten ziehen lassen und mit Salz abschmecken."
        ),
        "notes": "Dazu passen Reis, Fladenbrot oder ein Klecks Naturjoghurt.",
        "ingredients": (
            ("Rote Linsen", "300", "g", "abgespült"),
            ("Dosentomaten", "400", "g", "gehackt"),
            ("Kokosmilch", "400", "ml", ""),
            ("Spinat", "200", "g", ""),
            ("Zwiebel", "120", "g", "fein gewürfelt"),
            ("Knoblauch", "10", "g", "fein gehackt"),
            ("Rapsöl", "15", "ml", ""),
        ),
    },
    {
        "profile": "bazkit-veggie",
        "name": "Mediterraner Kichererbsensalat",
        "description": "Ein frischer, sättigender Salat für Mittagspause oder Picknick.",
        "servings": 4,
        "preparation_time": 20,
        "category": "lunch",
        "instructions": (
            "1. Kichererbsen abspülen und gründlich abtropfen lassen.\n"
            "2. Gurke, Tomaten und Paprika würfeln, Feta zerbröseln.\n"
            "3. Zitronensaft mit Olivenöl verrühren und über die Zutaten geben.\n"
            "4. Alles behutsam vermengen und vor dem Servieren zehn Minuten ziehen lassen."
        ),
        "notes": "Der Salat hält sich gut verschlossen bis zum nächsten Tag im Kühlschrank.",
        "ingredients": (
            ("Kichererbsen", "480", "g", "abgetropft"),
            ("Gurke", "300", "g", "gewürfelt"),
            ("Tomate", "300", "g", "gewürfelt"),
            ("Paprika rot", "200", "g", "gewürfelt"),
            ("Feta", "180", "g", "zerbröselt"),
            ("Zitronensaft", "40", "ml", "frisch gepresst"),
            ("Olivenöl", "30", "ml", ""),
        ),
    },
    {
        "profile": "bazkit-veggie",
        "name": "Pilzrisotto mit Parmesan",
        "description": "Cremiges Risotto mit gebratenen Champignons und frischem Spinat.",
        "servings": 4,
        "preparation_time": 40,
        "category": "dinner",
        "instructions": (
            "1. Champignons in Scheiben schneiden und in der Hälfte der Butter kräftig anbraten. Herausnehmen.\n"
            "2. Zwiebel in der restlichen Butter glasig dünsten, Reis zugeben und kurz mitrösten.\n"
            "3. Nach und nach heißes Wasser zugießen und dabei regelmäßig rühren, bis der Reis cremig ist.\n"
            "4. Champignons, Spinat und Parmesan unterheben und sofort servieren."
        ),
        "notes": "Die Flüssigkeit immer erst nachgießen, wenn der Reis sie fast aufgenommen hat.",
        "ingredients": (
            ("Reis", "320", "g", "am besten Rundkornreis"),
            ("Champignon", "400", "g", "in Scheiben"),
            ("Zwiebel", "100", "g", "fein gewürfelt"),
            ("Spinat", "120", "g", ""),
            ("Parmesan", "80", "g", "frisch gerieben"),
            ("Butter", "40", "g", ""),
        ),
    },
    {
        "profile": "bazkit-weltkueche",
        "name": "Teriyaki-Lachs mit Brokkoli",
        "description": "Lachs in einer glänzenden japanisch inspirierten Sauce mit Reis und Brokkoli.",
        "servings": 4,
        "preparation_time": 35,
        "category": "dinner",
        "instructions": (
            "1. Reis nach Packungsangabe garen und Brokkoli bissfest dämpfen.\n"
            "2. Helle Sojasauce, Sake und Honig in einer Pfanne zwei Minuten einkochen.\n"
            "3. Lachs einlegen und je nach Dicke drei bis fünf Minuten pro Seite garen.\n"
            "4. Sauce über den Lachs geben und zusammen mit Reis und Brokkoli anrichten."
        ),
        "notes": "Die Sauce nur sanft reduzieren, damit sie nicht zu salzig wird.",
        "ingredients": (
            ("Lachs", "600", "g", "in vier Portionen"),
            ("Reis", "300", "g", ""),
            ("Brokkoli", "400", "g", "in Röschen"),
            ("Helle Sojasauce", "60", "ml", ""),
            ("Sake", "40", "ml", "Koch-Sake"),
            ("Honig", "30", "g", ""),
        ),
    },
    {
        "profile": "bazkit-weltkueche",
        "name": "Tofu-Gemüse-Wok mit dunkler Sojasauce",
        "description": "Knuspriger Tofu und knackiges Gemüse mit einer aromatischen Woksauce.",
        "servings": 4,
        "preparation_time": 30,
        "category": "dinner",
        "instructions": (
            "1. Tofu trocken tupfen, würfeln und im Rapsöl rundherum goldbraun braten.\n"
            "2. Paprika und Brokkoli zugeben und bei hoher Hitze vier Minuten mitbraten.\n"
            "3. Helle und dunkle Sojasauce mit Sesamöl verrühren und in den Wok geben.\n"
            "4. Kurz durchschwenken und mit frisch gekochtem Reis servieren."
        ),
        "notes": "Dunkle Sojasauce sorgt für Farbe, helle Sojasauce für die Würze.",
        "ingredients": (
            ("Tofu", "400", "g", "fest"),
            ("Reis", "300", "g", ""),
            ("Brokkoli", "300", "g", "in kleinen Röschen"),
            ("Paprika rot", "250", "g", "in Streifen"),
            ("Helle Sojasauce", "35", "ml", ""),
            ("Dunkle Sojasauce", "20", "ml", ""),
            ("Geröstetes Sesamöl", "10", "ml", ""),
            ("Rapsöl", "15", "ml", "zum Braten"),
        ),
    },
    {
        "profile": "bazkit-weltkueche",
        "name": "Shakshuka mit Feta",
        "description": "Eier in würziger Tomaten-Paprika-Sauce – ideal zum Teilen.",
        "servings": 4,
        "preparation_time": 35,
        "category": "dinner",
        "instructions": (
            "1. Zwiebel und Paprika würfeln und im Olivenöl acht Minuten weich braten.\n"
            "2. Knoblauch und Dosentomaten zugeben und die Sauce zehn Minuten einkochen.\n"
            "3. Vier Mulden formen, Eier hineinschlagen und zugedeckt sechs bis acht Minuten stocken lassen.\n"
            "4. Feta darüberbröseln und direkt aus der Pfanne servieren."
        ),
        "notes": "Mit Brot servieren, um die Tomatensauce aufzunehmen.",
        "ingredients": (
            ("Dosentomaten", "800", "g", "gehackt"),
            ("Ei", "4", "Stück", ""),
            ("Paprika rot", "250", "g", "gewürfelt"),
            ("Zwiebel", "120", "g", "gewürfelt"),
            ("Knoblauch", "10", "g", "fein gehackt"),
            ("Feta", "150", "g", ""),
            ("Olivenöl", "20", "ml", ""),
        ),
    },
    {
        "profile": "bazkit-backstube",
        "name": "Saftige Bananen-Hafer-Muffins",
        "description": "Weiche Muffins mit Banane und Haferflocken für Frühstück oder Pause.",
        "servings": 12,
        "preparation_time": 35,
        "category": "snack",
        "instructions": (
            "1. Backofen auf 180 °C Ober-/Unterhitze vorheizen und ein Muffinblech vorbereiten.\n"
            "2. Bananen zerdrücken und mit Eiern, Milch und geschmolzener Butter verrühren.\n"
            "3. Mehl, Haferflocken und Zucker kurz unterheben, bis gerade ein Teig entsteht.\n"
            "4. Auf zwölf Mulden verteilen und etwa 22 Minuten goldbraun backen."
        ),
        "notes": "Sehr reife Bananen geben den Muffins mehr Süße und Aroma.",
        "ingredients": (
            ("Banane", "300", "g", "sehr reif, ohne Schale"),
            ("Haferflocken", "150", "g", ""),
            ("Weizenmehl Type 405", "180", "g", ""),
            ("Ei", "2", "Stück", ""),
            ("Milch", "120", "ml", ""),
            ("Butter", "80", "g", "geschmolzen"),
            ("Zucker", "60", "g", ""),
        ),
    },
    {
        "profile": "bazkit-backstube",
        "name": "Apfel-Zimt-Crumble",
        "description": "Warme Äpfel unter knusprigen Butterstreuseln – schlicht und gemütlich.",
        "servings": 6,
        "preparation_time": 45,
        "category": "dessert",
        "instructions": (
            "1. Backofen auf 190 °C Ober-/Unterhitze vorheizen und eine Form einfetten.\n"
            "2. Äpfel würfeln, mit der Hälfte des Zuckers und etwas Zimt mischen und in die Form geben.\n"
            "3. Mehl, Haferflocken, restlichen Zucker und kalte Butter zu Streuseln verkneten.\n"
            "4. Streusel verteilen und 30 Minuten goldbraun backen."
        ),
        "notes": "Schmeckt warm besonders gut mit Naturjoghurt.",
        "ingredients": (
            ("Apfel", "900", "g", "entkernt und gewürfelt"),
            ("Weizenmehl Type 405", "160", "g", ""),
            ("Haferflocken", "100", "g", ""),
            ("Butter", "140", "g", "kalt, in Würfeln"),
            ("Zucker", "100", "g", ""),
            ("Zimt", "5", "g", ""),
        ),
    },
    {
        "profile": "bazkit-backstube",
        "name": "Fluffige Frühstückspfannkuchen",
        "description": "Ein einfaches Grundrezept für goldbraune, lockere Pfannkuchen.",
        "servings": 4,
        "preparation_time": 25,
        "category": "breakfast",
        "instructions": (
            "1. Mehl, Zucker und Salz in einer Schüssel mischen.\n"
            "2. Eier und Milch verquirlen, zu den trockenen Zutaten geben und glatt rühren.\n"
            "3. Die Hälfte der Butter schmelzen und unter den Teig rühren.\n"
            "4. Restliche Butter portionsweise in einer Pfanne erhitzen und die Pfannkuchen goldbraun ausbacken."
        ),
        "notes": "Den Teig vor dem Backen zehn Minuten ruhen lassen.",
        "ingredients": (
            ("Weizenmehl Type 405", "250", "g", ""),
            ("Milch", "400", "ml", ""),
            ("Ei", "3", "Stück", ""),
            ("Zucker", "30", "g", ""),
            ("Butter", "50", "g", ""),
            ("Salz", "2", "g", ""),
        ),
    },
)
