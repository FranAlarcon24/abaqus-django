from django.core.management.base import BaseCommand
from portfolios.services.weights import create_initial_holdings_from_excel


class Command(BaseCommand):
    help = "Create initial holdings (Ci,0) from Weights sheet"

    def handle(self, *args, **options):
        create_initial_holdings_from_excel("datos.xlsx")
        self.stdout.write(
            self.style.SUCCESS("Initial holdings created successfully")
        )
