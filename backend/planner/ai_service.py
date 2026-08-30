import json
from collections import Counter

from django.conf import settings
from openai import OpenAI


MEAL_CATEGORY_PRIORITY = {
    "breakfast": ("breakfast", "snack", "dessert", "other", "lunch", "dinner"),
    "lunch": ("lunch", "dinner", "other", "snack", "breakfast", "dessert"),
    "dinner": ("dinner", "lunch", "other", "snack", "breakfast", "dessert"),
}
MEAL_TARGET_SHARE = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.40}


def recipe_number(recipe, field):
    value = getattr(recipe, field, None)
    return float(value) if value is not None else 0.0


def plan_recipe_slots_automatically(recipes, slots, preferences=None):
    """Create a deterministic, varied plan using nutrition-ready saved recipes."""
    preferences = preferences or {}
    if not recipes or not slots:
        return {}

    max_repeats = max(int(preferences.get("max_recipe_repeats") or 2), 1)
    calorie_target = preferences.get("daily_calorie_target")
    protein_target = preferences.get("daily_protein_target")
    selected_types = set(preferences.get("meal_types") or MEAL_TARGET_SHARE)
    share_total = sum(MEAL_TARGET_SHARE[item] for item in selected_types) or 1
    counts = Counter()
    assignments = {}
    last_recipe_id = None

    for day, meal_type in slots:
        priorities = MEAL_CATEGORY_PRIORITY[meal_type]
        meal_share = MEAL_TARGET_SHARE[meal_type] / share_total

        def score(recipe):
            category_score = priorities.index(recipe.category) * 10000
            repeat_score = counts[recipe.id] * 1600
            adjacent_score = 3500 if recipe.id == last_recipe_id else 0
            over_limit_score = 50000 if counts[recipe.id] >= max_repeats else 0
            nutrition_score = 0.0
            if calorie_target:
                desired = max(float(calorie_target) * meal_share, 1)
                nutrition_score += abs(recipe_number(recipe, "calories") - desired) * 2
            if protein_target:
                desired = max(float(protein_target) * meal_share, 1)
                nutrition_score += abs(recipe_number(recipe, "protein") - desired) * 8
            return (
                over_limit_score + category_score + repeat_score + adjacent_score + nutrition_score,
                counts[recipe.id],
                recipe.name.casefold(),
                recipe.id,
            )

        # If the collection is too small, exceeding the requested repeat count is
        # preferable to leaving a day empty.
        recipe = min(recipes, key=score)
        key = (day.isoformat(), meal_type)
        assignments[key] = recipe.id
        counts[recipe.id] += 1
        last_recipe_id = recipe.id

    return assignments


def plan_recipe_slots_with_ai(recipes, slots, preferences=None):
    """Return a validated slot-to-recipe mapping or an empty mapping as fallback."""
    preferences = preferences or {}
    if not slots or not getattr(settings, "OPENAI_API_KEY", ""):
        return {}

    recipe_ids = [recipe.id for recipe in recipes]
    recipe_data = [
        {
            "id": recipe.id,
            "name": recipe.name,
            "category": recipe.category,
            "calories_per_serving": float(recipe.calories) if recipe.calories is not None else None,
            "protein_per_serving": float(recipe.protein) if recipe.protein is not None else None,
            "carbohydrates_per_serving": float(recipe.carbohydrates),
            "fat_per_serving": float(recipe.fat),
            "fiber_per_serving": float(recipe.fiber),
        }
        for recipe in recipes
    ]
    slot_data = [
        {"date": day.isoformat(), "meal_type": meal_type}
        for day, meal_type in slots
    ]
    prompt = (
        "Plane die freien Plätze eines deutschen Wochenplans ausschließlich mit den "
        "vorhandenen Rezepten. Ordne Frühstücksrezepte bevorzugt dem Frühstück und "
        "Mittag-/Abendessen passend zu. Sorge für Abwechslung, vermeide dasselbe Rezept "
        "an direkt aufeinanderfolgenden Plätzen. Alle bereitgestellten Rezepte besitzen "
        "vollständige Nährwerte. Berücksichtige die Zielwerte als Tagesziel pro Person. "
        "Jeder angegebene Platz muss genau einmal vorkommen.\n\n"
        f"Planungswünsche:\n{json.dumps(preferences, ensure_ascii=False, default=str)}\n\n"
        f"Rezepte:\n{json.dumps(recipe_data, ensure_ascii=False)}\n\n"
        f"Freie Plätze:\n{json.dumps(slot_data, ensure_ascii=False)}"
    )

    try:
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=20.0,
            max_retries=1,
        )
        response = client.responses.create(
            model=getattr(settings, "OPENAI_PLANNER_MODEL", settings.OPENAI_RECIPE_MODEL),
            input=[
                {
                    "role": "system",
                    "content": (
                        "Du planst Mahlzeiten für bazkit. Verwende ausschließlich die "
                        "bereitgestellten Rezept-IDs und antworte nur mit gültigem JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "weekly_recipe_plan",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "assignments": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "date": {"type": "string"},
                                        "meal_type": {
                                            "type": "string",
                                            "enum": ["breakfast", "lunch", "dinner"],
                                        },
                                        "recipe_id": {
                                            "type": "integer",
                                            "enum": recipe_ids,
                                        },
                                    },
                                    "required": ["date", "meal_type", "recipe_id"],
                                    "additionalProperties": False,
                                },
                            }
                        },
                        "required": ["assignments"],
                        "additionalProperties": False,
                    },
                }
            },
        )
        result = json.loads(response.output_text)
    except Exception:
        return {}

    allowed_slots = {(day.isoformat(), meal_type) for day, meal_type in slots}
    allowed_recipe_ids = set(recipe_ids)
    assignments = {}
    for item in result.get("assignments", []):
        key = (str(item.get("date", "")), str(item.get("meal_type", "")))
        recipe_id = item.get("recipe_id")
        if key in allowed_slots and recipe_id in allowed_recipe_ids:
            assignments[key] = recipe_id

    if len(assignments) != len(allowed_slots):
        return {}
    max_repeats = max(int(preferences.get("max_recipe_repeats") or 2), 1)
    counts = Counter(assignments.values())
    if len(recipes) * max_repeats >= len(allowed_slots) and any(
        count > max_repeats for count in counts.values()
    ):
        return {}
    return assignments
