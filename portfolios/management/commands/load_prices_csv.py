from django.core.management.base import BaseCommand
from portfolios.services.etl import load_prices_from_csv


class Command(BaseCommand):
    help = "Load prices from one or more CSV files (wide or long format)"

    def add_arguments(self, parser):
        parser.add_argument("files", nargs="+", help="CSV file paths (e.g., 2022.csv 2023.csv)")

    def handle(self, *args, **options):
        files = options["files"]
        count = load_prices_from_csv(files)
        self.stdout.write(self.style.SUCCESS(f"Loaded {count} prices from {len(files)} file(s)"))
