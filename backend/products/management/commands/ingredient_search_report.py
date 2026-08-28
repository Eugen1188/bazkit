from django.core.management.base import BaseCommand

from products.models import IngredientSearchMetric


class Command(BaseCommand):
    help = "Zeigt aggregierte Suchlücken und gewählte Zutaten ohne personenbezogene Daten."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=50)
        parser.add_argument("--all", action="store_true", help="Zeigt auch gelöste Einträge.")

    def handle(self, *args, **options):
        limit = max(1, min(500, options["limit"]))
        metrics = IngredientSearchMetric.objects.select_related("last_selected_product")
        if not options["all"]:
            metrics = metrics.filter(review_status="open")
        metrics = metrics.order_by(
            "-zero_result_count", "-search_count", "normalized_query"
        )[:limit]

        self.stdout.write("ZUTATEN-SUCHLÜCKEN (ANONYM AGGREGIERT)")
        if not metrics:
            self.stdout.write("Keine offenen Suchlücken vorhanden.")
            return

        for metric in metrics:
            selected = (
                metric.last_selected_product.canonical_name
                or metric.last_selected_product.name
                if metric.last_selected_product
                else "—"
            )
            self.stdout.write(
                f"{metric.display_query} · {metric.context} · "
                f"Suchen {metric.search_count} · ohne Treffer {metric.zero_result_count} · "
                f"Auswahlen {metric.selection_count} · zuletzt gewählt {selected}"
            )
