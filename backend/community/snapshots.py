from lists.models import SavedList, SavedListItem
from recipes.models import Ingredients, Recipe
from recipes.storage import delete_recipe_image_if_unused


RECIPE_FIELDS = (
    "name",
    "description",
    "servings",
    "preparation_time",
    "category",
    "instructions",
    "notes",
    "image_key",
    "image_position_x",
    "image_position_y",
    "image_zoom",
    "calories",
    "protein",
    "carbohydrates",
    "fat",
    "fiber",
    "estimated_price",
)

INGREDIENT_FIELDS = (
    "product",
    "name",
    "quantity",
    "unit",
    "estimated_price",
    "price_source",
    "price_currency",
    "price_date",
    "price_store",
    "price_sample_count",
    "price_min",
    "price_max",
    "package_price",
    "package_quantity",
    "package_unit",
)

LIST_ITEM_FIELDS = (
    "product",
    "name",
    "quantity",
    "unit",
    "note",
    "estimated_price",
    "price_source",
    "price_currency",
    "price_date",
    "price_store",
    "price_sample_count",
    "price_min",
    "price_max",
    "package_price",
    "package_quantity",
    "package_unit",
)


def clone_recipe(source, user, *, community_snapshot=False):
    recipe = Recipe.objects.create(
        user=user,
        is_community_snapshot=community_snapshot,
        **{field: getattr(source, field) for field in RECIPE_FIELDS},
    )
    Ingredients.objects.bulk_create([
        Ingredients(
            recipe=recipe,
            **{field: getattr(item, field) for field in INGREDIENT_FIELDS},
        )
        for item in source.ingredients.all()
    ])
    return recipe


def clone_saved_list(source, user, *, community_snapshot=False):
    saved_list = SavedList.objects.create(
        user=user,
        title=source.title,
        is_community_snapshot=community_snapshot,
    )
    SavedListItem.objects.bulk_create([
        SavedListItem(
            saved_list=saved_list,
            **{field: getattr(item, field) for field in LIST_ITEM_FIELDS},
        )
        for item in source.items.all()
    ])
    return saved_list


def delete_post_snapshot(post):
    recipe = post.recipe if post.recipe_id and post.recipe.is_community_snapshot else None
    recipe_image_key = recipe.image_key if recipe is not None else ""
    saved_list = (
        post.saved_list
        if post.saved_list_id and post.saved_list.is_community_snapshot
        else None
    )
    post.delete()
    if recipe is not None:
        recipe.delete()
        delete_recipe_image_if_unused(recipe_image_key)
    if saved_list is not None:
        saved_list.delete()
