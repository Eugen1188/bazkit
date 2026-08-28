"""Feste USDA-SR-Legacy-Ergänzungen für Lücken im deutschen BLS.

Die Werte beziehen sich auf 100 g und stammen aus dem offiziellen USDA
FoodData-Central-SR-Legacy-Download (April 2018).
"""


def product(external_id, name, category, calories, protein, carbs, fat, fiber, unit="g"):
    return {
        "external_id": external_id,
        "name": name,
        "category": category,
        "default_unit": unit,
        "calories_per_100g": calories,
        "protein_per_100g": protein,
        "carbohydrates_per_100g": carbs,
        "fat_per_100g": fat,
        "fiber_per_100g": fiber,
    }


CURATED_USDA_PRODUCTS = (
    product("169997", "Koriander", "Kräuter", "23", "2.13", "3.67", "0.52", "2.8"),
    product("170922", "Koriandersamen", "Gewürze", "298", "12.37", "54.99", "17.77", "41.9"),
    product("170923", "Kreuzkümmel", "Gewürze", "375", "17.81", "44.24", "22.27", "10.5"),
    product("172231", "Kurkuma", "Gewürze", "312", "9.68", "67.14", "3.25", "22.7"),
    product("173470", "Thymian", "Kräuter", "101", "5.56", "24.45", "1.68", "14"),
    product("170938", "Thymian getrocknet", "Gewürze", "276", "9.11", "63.94", "7.43", "37"),
    product("173473", "Rosmarin", "Kräuter", "131", "3.31", "20.7", "5.86", "14.1"),
    product("171333", "Rosmarin getrocknet", "Gewürze", "331", "4.88", "64.06", "15.22", "42.6"),
    product("170928", "Majoran", "Gewürze", "271", "12.66", "60.56", "7.04", "40.3"),
    product("172233", "Dill", "Kräuter", "43", "3.46", "7.02", "1.12", "2.1"),
    product("170935", "Salbei", "Gewürze", "315", "10.63", "60.73", "12.75", "40.3"),
    product("170917", "Lorbeerblatt", "Gewürze", "313", "7.61", "74.97", "8.36", "26.3"),
    product("171326", "Muskatnuss", "Gewürze", "525", "5.84", "49.29", "36.31", "20.8"),
    product("171321", "Gewürznelke", "Gewürze", "274", "5.97", "65.53", "13", "33.9"),
    product("171320", "Zimt", "Gewürze", "247", "3.99", "80.59", "1.24", "53.1"),
    product("173471", "Vanilleextrakt", "Backzutaten", "288", "0.06", "12.65", "0.06", "0", "ml"),
    product("174531", "Fischsauce", "Würzsaucen", "35", "5.06", "3.64", "0.01", "0", "ml"),
    product("170919", "Kardamom", "Gewürze", "311", "10.76", "68.47", "6.7", "28"),
    product("170934", "Safran", "Gewürze", "310", "11.43", "65.37", "5.85", "3.9"),
    product("170931", "Schwarzer Pfeffer", "Gewürze", "251", "10.39", "63.95", "3.26", "25.3"),
    product("171329", "Paprikapulver", "Gewürze", "282", "14.14", "53.99", "12.89", "34.9"),
    product("171323", "Fenchelsamen", "Gewürze", "345", "15.8", "52.29", "14.87", "39.8"),
    product("170929", "Senfkörner", "Gewürze", "508", "26.08", "28.09", "36.24", "12.2"),
    product("171330", "Mohn", "Saaten", "525", "17.99", "28.13", "41.56", "19.5"),
    product("170554", "Chiasamen", "Saaten", "486", "16.54", "42.12", "30.74", "34.4"),
    product("170496", "Wakame", "Algen", "45", "3.03", "9.14", "0.64", "0.5"),
    product("168458", "Nori", "Algen", "35", "5.81", "5.11", "0.28", "0.3"),
    product("168576", "Jalapeño", "Gewürzgemüse", "29", "0.91", "6.5", "0.37", "2.8"),
    product("169698", "Maisstärke", "Stärke", "381", "0.26", "91.27", "0.05", "0.9"),
    product("175040", "Natron", "Backzutaten", "0", "0", "0", "0", "0"),
)
