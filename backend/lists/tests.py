from types import SimpleNamespace

from django.test import SimpleTestCase

from .categories import shopping_category


class ShoppingCategoryTests(SimpleTestCase):
    def category_for(self, name, category=""):
        product = SimpleNamespace(name=name, canonical_name=name, category=category)
        item = SimpleNamespace(name=name, product=product)
        return shopping_category(item)[0]

    def test_common_groceries_are_assigned_to_store_sections(self):
        self.assertEqual(self.category_for("Banane"), "produce")
        self.assertEqual(self.category_for("Vollmilch"), "dairy_eggs")
        self.assertEqual(self.category_for("Rind Hackfleisch"), "meat_fish")
        self.assertEqual(self.category_for("Spaghetti"), "pantry")
        self.assertEqual(self.category_for("Spülmittel"), "household")
