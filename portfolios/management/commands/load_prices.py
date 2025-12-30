from django.core.management.base import BaseCommand
from portfolios.services.etl import load_prices_from_excel


class Command(BaseCommand):
    help = "Load prices from datos.xlsx"

    def handle(self, *args, **options):
        count = load_prices_from_excel("datos.xlsx")
        self.stdout.write(self.style.SUCCESS(f"Loaded {count} prices"))
