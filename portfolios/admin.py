from django.contrib import admin

# Register your models here.

from django.contrib import admin
from portfolios.models import Asset, Portfolio, Price, Holding

admin.site.register(Asset)
admin.site.register(Portfolio)
admin.site.register(Price)
admin.site.register(Holding)
