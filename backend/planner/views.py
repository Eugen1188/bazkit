from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lists.models import ShoppingList, ShoppingListItem
from lists.serializers import ShoppingListSerializer
from products.pricing import scaled_price
from recipes.models import Recipe

from .ai_service import plan_recipe_slots_with_ai
from .models import WeeklyPlanEntry
from .serializers import WeeklyPlanEntrySerializer


PRICE_SNAPSHOT_FIELDS = (
    "price_source",
    "price_currency",
    "price_date",
    "price_store",
    "price_sample_count",
    "package_price",
    "package_quantity",
    "package_unit",
)
MEAL_TYPES = ("breakfast", "lunch", "dinner")


def current_week_start():
    today = date.today()
    return today - timedelta(days=today.weekday())


def request_range(request, default_days=7):
    start_value = request.query_params.get("start") or request.data.get("start")
    end_value = request.query_params.get("end") or request.data.get("end")
    start = parse_date(str(start_value)) if start_value else current_week_start()
    end = parse_date(str(end_value)) if end_value else start + timedelta(days=default_days - 1)

    if start is None or end is None:
        raise ValueError("Start und Ende müssen gültige Datumswerte im Format JJJJ-MM-TT sein.")
    if end < start:
        raise ValueError("Das Enddatum darf nicht vor dem Startdatum liegen.")
    if (end - start).days > 31:
        raise ValueError("Es können höchstens 32 Tage gleichzeitig geladen werden.")
    return start, end


def entries_for_range(user, start, end):
    return (
        WeeklyPlanEntry.objects
        .filter(user=user, date__range=(start, end))
        .select_related("recipe")
        .prefetch_related("recipe__ingredients")
        .order_by("date", "meal_type")
    )


def serialize_entries(entries, request):
    return WeeklyPlanEntrySerializer(
        entries,
        many=True,
        context={"request": request},
    ).data


class WeeklyPlanEntryListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            start, end = request_range(request)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        entries = entries_for_range(request.user, start, end)
        return Response(serialize_entries(entries, request))

    @transaction.atomic
    def post(self, request):
        serializer = WeeklyPlanEntrySerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        entry = WeeklyPlanEntry.objects.create(
            user=request.user,
            date=values["date"],
            meal_type=values["meal_type"],
            recipe=values["recipe"],
            servings=values.get("servings") or max(values["recipe"].servings, 1),
        )
        entry = (
            WeeklyPlanEntry.objects
            .select_related("recipe")
            .prefetch_related("recipe__ingredients")
            .get(pk=entry.pk)
        )
        return Response(
            WeeklyPlanEntrySerializer(entry, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class WeeklyPlanEntryDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return (
            WeeklyPlanEntry.objects
            .filter(pk=pk, user=request.user)
            .select_related("recipe")
            .prefetch_related("recipe__ingredients")
            .first()
        )

    def patch(self, request, pk):
        entry = self.get_object(request, pk)
        if entry is None:
            return Response(
                {"detail": "Der geplante Eintrag wurde nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = WeeklyPlanEntrySerializer(
            entry,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)

    def delete(self, request, pk):
        entry = self.get_object(request, pk)
        if entry is None:
            return Response(
                {"detail": "Der geplante Eintrag wurde nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND,
            )
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WeeklyPlanGenerateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            start, end = request_range(request)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        if (end - start).days != 6:
            return Response(
                {"detail": "Die automatische Planung benötigt genau sieben Tage."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipes = list(
            Recipe.objects
            .filter(user=request.user, is_community_snapshot=False)
            .prefetch_related("ingredients")
            .order_by("category", "name", "id")
            [:120]
        )
        if not recipes:
            return Response(
                {"detail": "Erstelle zuerst mindestens ein Rezept, damit deine Woche geplant werden kann."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        overwrite = bool(request.data.get("overwrite", False))
        occupied_slots = {
            (entry.date, entry.meal_type)
            for entry in WeeklyPlanEntry.objects.filter(
                user=request.user,
                date__range=(start, end),
            )
        }
        category_priority = {
            "breakfast": ("breakfast", "snack", "dessert", "other"),
            "lunch": ("lunch", "dinner", "other", "snack"),
            "dinner": ("dinner", "lunch", "other"),
        }
        pools = {}
        for meal_type, priorities in category_priority.items():
            pool = [recipe for category in priorities for recipe in recipes if recipe.category == category]
            pools[meal_type] = pool or recipes

        counters = defaultdict(int)
        slots_to_plan = []
        day = start
        while day <= end:
            for meal_type in MEAL_TYPES:
                if (day, meal_type) not in occupied_slots or overwrite:
                    slots_to_plan.append((day, meal_type))
            day += timedelta(days=1)

        ai_assignments = plan_recipe_slots_with_ai(recipes, slots_to_plan)
        recipes_by_id = {recipe.id: recipe for recipe in recipes}
        changed = 0
        day = start
        while day <= end:
            for meal_type in MEAL_TYPES:
                has_entries = (day, meal_type) in occupied_slots
                if has_entries and not overwrite:
                    continue
                pool = pools[meal_type]
                recipe = recipes_by_id.get(
                    ai_assignments.get((day.isoformat(), meal_type))
                ) or pool[counters[meal_type] % len(pool)]
                counters[meal_type] += 1
                if overwrite:
                    WeeklyPlanEntry.objects.filter(
                        user=request.user,
                        date=day,
                        meal_type=meal_type,
                    ).delete()
                WeeklyPlanEntry.objects.create(
                    user=request.user,
                    date=day,
                    meal_type=meal_type,
                    recipe=recipe,
                    servings=max(recipe.servings, 1),
                )
                changed += 1
            day += timedelta(days=1)

        entries = entries_for_range(request.user, start, end)
        return Response({
            "entries": serialize_entries(entries, request),
            "changed_count": changed,
            "planning_method": "ai" if ai_assignments else "automatic",
            "message": (
                "Deine Woche wurde abwechslungsreich geplant."
                if changed
                else "Alle Mahlzeiten dieser Woche sind bereits geplant."
            ),
        })


class WeeklyPlanShoppingListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        try:
            start, end = request_range(request)
        except ValueError as error:
            return Response({"detail": str(error)}, status=status.HTTP_400_BAD_REQUEST)

        entries = list(entries_for_range(request.user, start, end))
        if not entries:
            return Response(
                {"detail": "Plane zuerst mindestens eine Mahlzeit für diese Woche."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        grouped = {}
        ingredient_lines = 0
        for entry in entries:
            recipe_servings = Decimal(entry.recipe.servings or 1)
            factor = Decimal(entry.servings) / recipe_servings
            for ingredient in entry.recipe.ingredients.all():
                ingredient_lines += 1
                product_id = ingredient.product_id
                name = ingredient.name or (ingredient.product.name if ingredient.product else "Zutat")
                unit = str(ingredient.unit or "").strip()
                key = (product_id or name.casefold(), unit.casefold())
                if key not in grouped:
                    grouped[key] = {
                        "product": ingredient.product,
                        "name": name,
                        "unit": unit,
                        "quantity": Decimal("0") if ingredient.quantity is not None else None,
                        "fallback_price": Decimal("0"),
                        "has_fallback_price": False,
                        "snapshot": {
                            field: getattr(ingredient, field)
                            for field in PRICE_SNAPSHOT_FIELDS
                        },
                    }
                item = grouped[key]
                if ingredient.quantity is not None:
                    if item["quantity"] is None:
                        item["quantity"] = Decimal("0")
                    item["quantity"] += ingredient.quantity * factor
                if ingredient.estimated_price is not None:
                    item["fallback_price"] += ingredient.estimated_price * factor
                    item["has_fallback_price"] = True
                if item["snapshot"]["package_price"] is None and ingredient.package_price is not None:
                    item["snapshot"] = {
                        field: getattr(ingredient, field)
                        for field in PRICE_SNAPSHOT_FIELDS
                    }

        shopping_list, _ = ShoppingList.objects.get_or_create(user=request.user)
        new_items = []
        for item in grouped.values():
            snapshot = item["snapshot"]
            estimated_price = None
            if snapshot["package_price"] is not None:
                estimated_price = scaled_price(
                    snapshot["package_price"],
                    snapshot["package_quantity"],
                    snapshot["package_unit"],
                    item["quantity"],
                    item["unit"],
                    mode="purchase",
                )
            elif item["has_fallback_price"]:
                estimated_price = item["fallback_price"]

            new_items.append(ShoppingListItem(
                shopping_list=shopping_list,
                product=item["product"],
                name=item["name"][:100],
                quantity=(
                    item["quantity"].quantize(Decimal("0.01"))
                    if item["quantity"] is not None
                    else None
                ),
                unit=item["unit"][:30],
                note=f"Wochenplan {start.strftime('%d.%m.')}–{end.strftime('%d.%m.%Y')}",
                is_checked=False,
                estimated_price=(
                    estimated_price.quantize(Decimal("0.01"))
                    if estimated_price is not None
                    else None
                ),
                price_min=None,
                price_max=None,
                **snapshot,
            ))

        ShoppingListItem.objects.bulk_create(new_items)
        shopping_list = (
            ShoppingList.objects
            .prefetch_related("items")
            .get(pk=shopping_list.pk)
        )
        return Response({
            "shopping_list": ShoppingListSerializer(shopping_list).data,
            "meal_count": len(entries),
            "ingredient_count": ingredient_lines,
            "product_count": len(new_items),
            "message": f"{len(new_items)} Produkte wurden zur Einkaufsliste hinzugefügt.",
        })
