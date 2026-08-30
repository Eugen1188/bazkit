from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from .catalog import (
    AVERAGE_UNIT_WEIGHT_GRAMS,
    canonical_recipe_name,
    canonical_search_query,
    curated_unit_conversion,
    ingredient_quantity_grams,
    recipe_ingredient_status,
    suggested_unit_for_product,
    sync_curated_unit_conversion,
)
from .ingredient_catalog import (
    INGREDIENT_DEFINITIONS,
    canonical_query,
    definition_for_query,
    display_name_for_query,
    normalize_alias,
    replace_product_aliases,
)
from .models import IngredientPriceReference, IngredientSearchMetric, Product, ProductUnitConversion
from .legacy_normalization import parse_legacy_product_name
from .nutrition_quality import apply_safe_zero_defaults, nutrition_is_complete
from .pricing import estimate_product_price
from .serializers import ProductSerializer
from .shopping_taxonomy import infer_product_taxonomy
from .views import (
    ExternalProductSearchAPIView,
    IngredientSearchFeedbackAPIView,
    ProductSearchAPIView,
    usda_payload,
)


COMPLETE_NUTRITION = {
    "calories_per_100g": Decimal("20.00"),
    "protein_per_100g": Decimal("1.00"),
    "carbohydrates_per_100g": Decimal("3.00"),
    "fat_per_100g": Decimal("0.20"),
    "fiber_per_100g": Decimal("1.00"),
}


class RecipeCatalogTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="catalog-test",
            email="catalog@example.com",
            password="test-password",
        )

    def test_every_curated_definition_has_one_unambiguous_nutrition_source(self):
        alias_owners = {}
        for definition in INGREDIENT_DEFINITIONS:
            self.assertTrue(
                definition.preferred_bls_codes or definition.preferred_usda_ids,
                f"{definition.canonical_name} hat keine geprüfte Nährwertquelle.",
            )
            for alias in (definition.canonical_name, *definition.aliases):
                normalized = normalize_alias(alias)
                previous = alias_owners.setdefault(normalized, definition.canonical_name)
                self.assertEqual(
                    previous,
                    definition.canonical_name,
                    f"{alias} ist mehreren Zutaten zugeordnet.",
                )

    def test_piece_units_require_product_specific_sourced_conversion(self):
        product = Product.objects.create(name="Knoblauch", source="bls", external_id="garlic")
        self.assertIsNone(ingredient_quantity_grams("Knoblauch", 2, "Zehe", product=product))
        ProductUnitConversion.objects.create(
            product=product, unit="Zehe", grams_per_unit=Decimal("3"),
            source="MRI/BLS Begleitdaten", confidence="reference",
        )
        self.assertEqual(
            ingredient_quantity_grams("Knoblauch", 2, "Zehe", product=product), Decimal("6")
        )
        self.assertEqual(
            suggested_unit_for_product("Knoblauch", "Knoblauch", "produce"),
            "Zehe",
        )

    def test_curated_piece_conversions_cover_logical_catalog_items(self):
        expected = {
            "Apfel": ("Stück", Decimal("180")),
            "Kartoffel": ("Stück", Decimal("150")),
            "Kürbis": ("Stück", Decimal("1000")),
            "Ei": ("Stück", Decimal("60")),
            "Knoblauch": ("Zehe", Decimal("3")),
            "Staudensellerie": ("Stange", Decimal("40")),
            "Spargel": ("Stange", Decimal("20")),
        }
        for name, (unit, grams) in expected.items():
            conversion = curated_unit_conversion(name)
            self.assertIsNotNone(conversion)
            self.assertEqual(conversion["unit"], unit)
            self.assertEqual(conversion["grams_per_unit"], grams)

    def test_synced_pumpkin_piece_conversion_drives_nutrition_quantity(self):
        pumpkin = Product.objects.create(
            name="Kürbis", canonical_name="Kürbis", source="bls", external_id="pumpkin"
        )
        conversions = sync_curated_unit_conversion(pumpkin)
        self.assertEqual(conversions[0].unit, "Stück")
        self.assertEqual(conversions[0].grams_per_unit, Decimal("1000"))
        self.assertEqual(
            ingredient_quantity_grams("Kürbis", 1, "Stück", product=pumpkin),
            Decimal("1000"),
        )

    def test_canned_tomatoes_offer_only_calculable_package_units(self):
        tomatoes = Product.objects.create(
            name="Tomaten Konserve", canonical_name="Dosentomaten",
            source="bls", external_id="canned-tomatoes", default_unit="g",
        )
        sync_curated_unit_conversion(tomatoes)
        data = ProductSerializer(tomatoes).data
        self.assertEqual(data["available_units"], ["g", "kg", "Dose"])
        self.assertEqual(
            ingredient_quantity_grams("Dosentomaten", 1, "Dose", product=tomatoes),
            Decimal("400"),
        )

    def test_stem_vegetables_offer_stem_instead_of_unrelated_kitchen_units(self):
        celery = Product.objects.create(
            name="Staudensellerie roh", canonical_name="Staudensellerie",
            source="bls", external_id="celery", default_unit="Stange",
        )
        sync_curated_unit_conversion(celery)
        data = ProductSerializer(celery).data
        self.assertEqual(data["available_units"], ["g", "kg", "Stange"])
        self.assertEqual(
            ingredient_quantity_grams("Staudensellerie", 2, "Stange", product=celery),
            Decimal("80"),
        )

    def test_legacy_name_parser_separates_package_without_losing_name(self):
        parsed = parse_legacy_product_name("Passierte Tomaten 2 x 500 g")
        self.assertEqual(parsed.normalized_name, "Passierte Tomaten")
        self.assertEqual(parsed.package_count, 2)
        self.assertEqual(parsed.package_quantity, Decimal("500"))
        self.assertEqual(parsed.package_unit, "g")
        self.assertEqual(
            suggested_unit_for_product("Parmesan gerieben", "Parmesan", "dairy"),
            "g",
        )
        self.assertEqual(
            suggested_unit_for_product("Fischsauce", "Fischsauce", "pantry", "ml"),
            "ml",
        )
        garlic = Product.objects.create(
            name="Knoblauch roh",
            canonical_name="Knoblauch",
            default_unit="Stück",
        )
        self.assertIsNone(ProductSerializer(garlic).data["grams_per_unit"])
        self.assertTrue(all(weight > 0 for weight in AVERAGE_UNIT_WEIGHT_GRAMS.values()))

    def test_search_feedback_is_aggregated_without_user_data(self):
        for result_count in (0, 0, 3):
            request = APIRequestFactory().post(
                "/products/search-feedback/",
                {
                    "query": "Gemüsezwiebel",
                    "context": "recipe_create",
                    "event": "search",
                    "result_count": result_count,
                },
                format="json",
            )
            force_authenticate(request, user=self.user)
            response = IngredientSearchFeedbackAPIView.as_view()(request)
            self.assertEqual(response.status_code, 204)

        product = Product.objects.get(source="usda", external_id="170497")
        selection_request = APIRequestFactory().post(
            "/products/search-feedback/",
            {
                "query": "Gemüsezwiebel",
                "context": "recipe_create",
                "event": "selected",
                "product_id": product.id,
                "selected_rank": 2,
            },
            format="json",
        )
        force_authenticate(selection_request, user=self.user)
        selection_response = IngredientSearchFeedbackAPIView.as_view()(selection_request)
        self.assertEqual(selection_response.status_code, 204)

        metric = IngredientSearchMetric.objects.get(
            normalized_query="gemuesezwiebel",
            context="recipe_create",
        )
        self.assertEqual(metric.search_count, 3)
        self.assertEqual(metric.zero_result_count, 2)
        self.assertEqual(metric.selection_count, 1)
        self.assertEqual(metric.last_result_count, 3)
        self.assertEqual(metric.last_selected_rank, 2)
        self.assertEqual(metric.last_selected_product, product)
        self.assertEqual(metric.selection_counts, {str(product.id): 1})

    def test_catalog_classification_and_canonical_name(self):
        self.assertEqual(canonical_recipe_name("H-Milch fettarm, 1,5 % Fett"), "Fettarme Milch")
        self.assertEqual(canonical_recipe_name("Chilischoten, frisch"), "Chilischote")
        self.assertEqual(
            canonical_recipe_name("Bleichsellerie roh", "bls", "G220100"),
            "Staudensellerie",
        )
        self.assertEqual(
            canonical_recipe_name("Knollensellerie roh", "bls", "G660100"),
            "Knollensellerie",
        )
        self.assertEqual(canonical_search_query("Chilischotten"), "Chilischote")
        self.assertEqual(canonical_search_query("Peperoni"), "Chilischote")
        self.assertEqual(recipe_ingredient_status("Kürbissuppe mit Kokosmilch")[0], False)
        self.assertEqual(recipe_ingredient_status("Chili sin carne")[0], False)
        self.assertEqual(recipe_ingredient_status("Chili con carne einfach")[0], False)
        self.assertEqual(recipe_ingredient_status("Hähnchenbrust, roh")[0], True)
        self.assertEqual(recipe_ingredient_status("Rotweinkuchen")[0], False)
        self.assertEqual(recipe_ingredient_status("Rotweinpunsch")[0], False)

    def test_recipe_search_shows_chili_pepper_and_hides_stale_chili_meals(self):
        curated_chili = Product.objects.get(
            source="usda",
            external_id="170497",
        )
        self.assertTrue(curated_chili.is_recipe_ingredient)
        self.assertEqual(curated_chili.calories_per_100g, Decimal("40.00"))
        Product.objects.create(
            name="Chili sin carne",
            canonical_name="Chili sin carne",
            source="bls",
            external_id="X4A8000",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Chili", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "Chilischote")
        self.assertNotIn("Chili sin carne", [item["name"] for item in response.data])

        typo_request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Chilischotten", "recipe_only": "1"},
        )
        force_authenticate(typo_request, user=self.user)
        typo_response = ProductSearchAPIView.as_view()(typo_request)
        self.assertEqual(typo_response.data[0]["name"], "Chilischote")

    def test_recipe_search_prioritizes_canonical_milk_and_hides_meals(self):
        Product.objects.create(
            name="H-Milch fettarm, 1,5 % Fett",
            canonical_name="Fettarme Milch",
            source="bls",
            external_id="M113200",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        Product.objects.create(
            name="Buttermilch",
            canonical_name="Buttermilch",
            source="bls",
            external_id="M150000",
            is_recipe_ingredient=True,
        )
        Product.objects.create(
            name="Kürbissuppe mit Kokosmilch",
            canonical_name="Kürbissuppe mit Kokosmilch",
            source="bls",
            external_id="X490263",
            is_recipe_ingredient=False,
        )
        request = APIRequestFactory().get("/products/search/", {"q": "Milch", "recipe_only": "1"})
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "Fettarme Milch")
        self.assertNotIn("Kürbissuppe mit Kokosmilch", [item["name"] for item in response.data])

    def test_staudensellerie_alias_selects_exact_complete_bls_ingredient(self):
        stalk = Product.objects.create(
            name="Bleichsellerie roh",
            canonical_name=canonical_recipe_name("Bleichsellerie roh", "bls", "G220100"),
            source="bls",
            external_id="G220100",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        root = Product.objects.create(
            name="Knollensellerie roh",
            canonical_name=canonical_recipe_name("Knollensellerie roh", "bls", "G660100"),
            source="bls",
            external_id="G660100",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        replace_product_aliases(stalk)
        replace_product_aliases(root)

        request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Staudensellerie", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.data], ["Staudensellerie"])
        self.assertTrue(response.data[0]["nutrition_complete"])

        alias_request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Bleichsellerie", "recipe_only": "1"},
        )
        force_authenticate(alias_request, user=self.user)
        alias_response = ProductSearchAPIView.as_view()(alias_request)

        self.assertEqual(alias_response.status_code, 200)
        self.assertEqual(alias_response.data[0]["name"], "Bleichsellerie")
        self.assertEqual(alias_response.data[0]["canonical_name"], "Staudensellerie")
        self.assertEqual(alias_response.data[0]["id"], response.data[0]["id"])

    def test_gemuesezwiebel_alias_selects_the_complete_onion_product(self):
        onion = Product.objects.create(
            name="Speisezwiebel roh",
            canonical_name="Zwiebel",
            source="bls",
            external_id="G480100",
            is_recipe_ingredient=True,
            shopping_category="produce",
            **COMPLETE_NUTRITION,
        )
        replace_product_aliases(onion)

        request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Gemüsezwiebel", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["name"] for item in response.data], ["Gemüsezwiebel"])
        self.assertEqual(response.data[0]["canonical_name"], "Zwiebel")
        self.assertEqual(response.data[0]["external_id"], "G480100")
        self.assertEqual(response.data[0]["shopping_category"], "produce")
        self.assertTrue(response.data[0]["nutrition_complete"])

    def test_shopping_taxonomy_separates_category_from_pantry_status(self):
        self.assertEqual(
            infer_product_taxonomy("Gemüsezwiebel", "Zwiebel"),
            ("produce", False),
        )
        self.assertEqual(
            infer_product_taxonomy("Speisesalz", "Salz"),
            ("pantry", True),
        )
        self.assertEqual(
            infer_product_taxonomy("Erbsen tiefgekühlt", "Erbse"),
            ("frozen", False),
        )
        self.assertEqual(
            infer_product_taxonomy("Tomaten Konserve", "Dosentomaten"),
            ("pantry", False),
        )
        self.assertEqual(
            infer_product_taxonomy("whey gold standard", "Whey Protein"),
            ("pantry", False),
        )
        self.assertEqual(
            infer_product_taxonomy("Star Aniseeds Sternanis", "Sternanis"),
            ("pantry", True),
        )

    def test_walnut_typo_and_prefix_find_generic_walnut_not_composite_products(self):
        walnut = Product.objects.create(
            name="Walnuss",
            canonical_name="Walnuss",
            source="bls",
            external_id="H120100",
            is_recipe_ingredient=True,
            calories_per_100g=Decimal("721.00"),
            protein_per_100g=Decimal("16.07"),
            carbohydrates_per_100g=Decimal("3.00"),
            fat_per_100g=Decimal("70.60"),
            fiber_per_100g=Decimal("4.60"),
        )
        Product.objects.create(
            name="Walnuss Glace",
            canonical_name="Walnuss Glace",
            source="open_food_facts",
            external_id="off-walnut-glace",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        replace_product_aliases(walnut)

        for query in ("Wallnuss", "Walln"):
            request = APIRequestFactory().get(
                "/products/search/",
                {"q": query, "recipe_only": "1"},
            )
            force_authenticate(request, user=self.user)
            response = ProductSearchAPIView.as_view()(request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual([item["name"] for item in response.data], ["Walnuss"])
            self.assertEqual(response.data[0]["external_id"], "H120100")
            self.assertTrue(response.data[0]["nutrition_complete"])

    def test_unknown_complete_bls_ingredient_is_found_despite_small_typo(self):
        parsnip = Product.objects.create(
            name="Pastinake roh",
            canonical_name="Pastinake",
            source="bls",
            external_id="G640100",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        replace_product_aliases(parsnip)
        request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Pastinakke", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["name"], "Pastinake")
        self.assertEqual(response.data[0]["external_id"], "G640100")

    def test_known_local_ingredient_skips_external_product_search(self):
        walnut = Product.objects.create(
            name="Walnuss",
            canonical_name="Walnuss",
            source="bls",
            external_id="H120100",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        replace_product_aliases(walnut)
        request = APIRequestFactory().get(
            "/products/external-search/",
            {"q": "Wallnuss", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)

        with patch("products.views.off_session") as session:
            response = ExternalProductSearchAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        session.assert_not_called()

    def test_rinderfond_and_rinderbruehe_share_one_nutrition_product(self):
        stock = Product.objects.create(
            name="Rinderbrühe",
            canonical_name="Rinderbrühe",
            source="bls",
            external_id="U985200",
            is_recipe_ingredient=True,
            calories_per_100g=Decimal("8.00"),
            protein_per_100g=Decimal("1.48"),
            carbohydrates_per_100g=Decimal("0.00"),
            fat_per_100g=Decimal("0.22"),
            fiber_per_100g=Decimal("0.00"),
        )
        replace_product_aliases(stock)

        ids = []
        for query, expected_name in (
            ("Rinderbrühe", "Rinderbrühe"),
            ("Rinderfond", "Rinderfond"),
        ):
            request = APIRequestFactory().get(
                "/products/search/",
                {"q": query, "recipe_only": "1"},
            )
            force_authenticate(request, user=self.user)
            response = ProductSearchAPIView.as_view()(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data[0]["name"], expected_name)
            self.assertEqual(response.data[0]["canonical_name"], "Rinderbrühe")
            ids.append(response.data[0]["id"])
        self.assertEqual(ids[0], ids[1])

    def test_extended_static_usda_ingredients_have_complete_nutrition(self):
        cumin = Product.objects.get(source="usda", external_id="170923")
        self.assertEqual(cumin.canonical_name, "Kreuzkümmel")
        self.assertTrue(cumin.has_complete_nutrition)
        self.assertEqual(cumin.protein_per_100g, Decimal("17.81"))
        self.assertEqual(definition_for_query("Cumin").canonical_name, "Kreuzkümmel")
        self.assertEqual(display_name_for_query("Cumin"), "Cumin")

        bamboo = Product.objects.get(source="usda", external_id="169210")
        self.assertEqual(bamboo.canonical_name, "Bambussprossen")
        self.assertTrue(bamboo.has_complete_nutrition)
        self.assertEqual(bamboo.fiber_per_100g, Decimal("2.20"))

    def test_safe_zero_defaults_complete_only_structural_zeroes(self):
        salmon = apply_safe_zero_defaults(
            "Lachs roh",
            "bls",
            "T410100",
            {
                "calories_per_100g": Decimal("200"),
                "protein_per_100g": Decimal("20"),
                "carbohydrates_per_100g": Decimal("0"),
                "fat_per_100g": Decimal("13"),
                "fiber_per_100g": None,
            },
        )
        self.assertEqual(salmon["fiber_per_100g"], Decimal("0"))
        self.assertTrue(nutrition_is_complete(salmon))

        acerola = apply_safe_zero_defaults(
            "Acerola roh",
            "bls",
            "F501100",
            {
                "calories_per_100g": Decimal("32"),
                "protein_per_100g": Decimal("0.4"),
                "carbohydrates_per_100g": Decimal("7.7"),
                "fat_per_100g": Decimal("0.3"),
                "fiber_per_100g": None,
            },
        )
        self.assertIsNone(acerola["fiber_per_100g"])

        dry_red_wine = apply_safe_zero_defaults(
            "Rotwein trocken",
            "bls",
            "P2A3000",
            {
                "calories_per_100g": Decimal("70"),
                "protein_per_100g": Decimal("0.22"),
                "carbohydrates_per_100g": Decimal("0.7"),
                "fat_per_100g": None,
                "fiber_per_100g": Decimal("0"),
            },
        )
        self.assertEqual(dry_red_wine["fat_per_100g"], Decimal("0"))
        self.assertTrue(nutrition_is_complete(dry_red_wine))

    def test_dry_red_wine_aliases_find_the_exact_complete_bls_product(self):
        wine = Product.objects.create(
            name="Rotwein trocken",
            canonical_name=canonical_recipe_name(
                "Rotwein trocken",
                "bls",
                "P2A3000",
            ),
            source="bls",
            external_id="P2A3000",
            default_unit="ml",
            is_recipe_ingredient=True,
            calories_per_100g=Decimal("70"),
            protein_per_100g=Decimal("0.22"),
            carbohydrates_per_100g=Decimal("0.7"),
            fat_per_100g=Decimal("0"),
            fiber_per_100g=Decimal("0"),
        )
        replace_product_aliases(wine)

        for query in ("Rotwein trocken", "trockener Rotwein", "Rotwein"):
            request = APIRequestFactory().get(
                "/products/search/",
                {"q": query, "recipe_only": "1"},
            )
            force_authenticate(request, user=self.user)
            response = ProductSearchAPIView.as_view()(request)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data[0]["name"], "Rotwein trocken")
            self.assertEqual(response.data[0]["external_id"], "P2A3000")
            self.assertEqual(response.data[0]["default_unit"], "ml")
            self.assertTrue(response.data[0]["nutrition_complete"])

    def test_curated_oregano_is_available_without_live_usda_request(self):
        oregano = Product.objects.get(source="usda", external_id="171328")
        self.assertEqual(oregano.canonical_name, "Oregano")
        self.assertTrue(oregano.has_complete_nutrition)

    def test_dosentomaten_alias_finds_one_complete_generic_ingredient(self):
        first = Product.objects.create(
            name="Tomaten, Konserve",
            canonical_name=canonical_recipe_name("Tomaten, Konserve"),
            source="bls",
            external_id="G520200",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        duplicate = Product.objects.create(
            name="Tomaten gehackt",
            canonical_name=canonical_recipe_name("Tomaten gehackt"),
            source="open_food_facts",
            external_id="123456789",
            is_recipe_ingredient=True,
            **COMPLETE_NUTRITION,
        )
        replace_product_aliases(first)
        replace_product_aliases(duplicate)

        request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Dosentomaten", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(canonical_query("Dosentomaten"), "Dosentomaten")
        self.assertEqual([item["name"] for item in response.data], ["Dosentomaten"])
        self.assertTrue(response.data[0]["nutrition_complete"])

    def test_incomplete_products_are_never_returned_for_recipes(self):
        product = Product.objects.create(
            name="Mangold roh",
            canonical_name="Mangold",
            source="bls",
            external_id="G480100",
            is_recipe_ingredient=True,
            calories_per_100g=Decimal("19.00"),
        )
        replace_product_aliases(product)
        request = APIRequestFactory().get(
            "/products/search/",
            {"q": "Mangold", "recipe_only": "1"},
        )
        force_authenticate(request, user=self.user)
        response = ProductSearchAPIView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_usda_payload_requires_and_maps_all_nutrients(self):
        product = usda_payload({
            "fdcId": 170457,
            "description": "Tomatoes, red, ripe, canned",
            "dataType": "SR Legacy",
            "foodNutrients": [
                {"nutrientId": 1008, "nutrientName": "Energy", "unitName": "KCAL", "value": 18},
                {"nutrientId": 1003, "nutrientName": "Protein", "unitName": "G", "value": 0.95},
                {"nutrientId": 1005, "nutrientName": "Carbohydrate, by difference", "unitName": "G", "value": 4.01},
                {"nutrientId": 1004, "nutrientName": "Total lipid (fat)", "unitName": "G", "value": 0.11},
                {"nutrientId": 1079, "nutrientName": "Fiber, total dietary", "unitName": "G", "value": 1.2},
            ],
        }, "Dosentomaten")
        self.assertEqual(product["name"], "Dosentomaten")
        self.assertTrue(nutrition_is_complete(product))
        self.assertEqual(product["source"], "usda")
        self.assertEqual(product["available_units"], ["g", "kg", "Dose"])
        self.assertEqual(product["unit_conversions"][0]["grams_per_unit"], "400")

    def test_reference_price_is_scaled_automatically(self):
        product = Product.objects.create(
            name="Tomate roh",
            canonical_name="Tomate",
            source="bls",
            external_id="G520100",
            is_recipe_ingredient=True,
        )
        IngredientPriceReference.objects.create(
            canonical_name="Tomate",
            category_tag="en:tomatoes",
            basis="kg",
            median_price=Decimal("3.00"),
            price_min=Decimal("2.50"),
            price_max=Decimal("3.50"),
            observation_count=12,
            location_count=4,
            confidence="high",
            is_active=True,
        )
        estimate = estimate_product_price(product, Decimal("250"), "g")
        self.assertTrue(estimate["available"])
        self.assertEqual(estimate["estimated_price"], Decimal("0.75"))
        self.assertEqual(estimate["price_source"], "open_prices_category")

    def test_low_confidence_reference_uses_average_piece_weight(self):
        product = Product.objects.create(
            name="Banane roh",
            canonical_name="Banane",
            source="bls",
            external_id="F110100",
            is_recipe_ingredient=True,
        )
        IngredientPriceReference.objects.create(
            canonical_name="Banane",
            category_tag="en:bananas",
            basis="kg",
            median_price=Decimal("2.00"),
            price_min=Decimal("1.50"),
            price_max=Decimal("2.50"),
            observation_count=1,
            location_count=1,
            confidence="low",
            is_active=True,
        )
        estimate = estimate_product_price(product, Decimal("1"), "Stück")
        self.assertTrue(estimate["available"])
        self.assertEqual(estimate["estimated_price"], Decimal("0.24"))
        self.assertEqual(estimate["confidence"], "low")
