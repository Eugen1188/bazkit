import json

from django.conf import settings
from openai import OpenAI


def plan_recipe_slots_with_ai(recipes, slots):
    """Return a validated slot-to-recipe mapping or an empty mapping as fallback."""
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
        "an direkt aufeinanderfolgenden Plätzen und berücksichtige Nährwerte, wenn sie "
        "vorhanden sind. Jeder angegebene Platz muss genau einmal vorkommen.\n\n"
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
    return assignments
