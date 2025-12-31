from django.contrib import admin

# Register your models here.

from django.contrib import admin
from portfolios.models import Asset, Portfolio, Price, Holding


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
	list_display = ("id", "name")
	search_fields = ("name",)
	ordering = ("name",)


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "initial_value")
	search_fields = ("name",)
	ordering = ("name",)


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
	list_display = ("id", "portfolio", "asset", "quantity")
	list_filter = ("portfolio", "asset")
	search_fields = ("portfolio__name", "asset__name")


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
	list_display = ("id", "asset", "date", "price")
	list_filter = ("asset", "date")
	search_fields = ("asset__name",)
	date_hierarchy = "date"
