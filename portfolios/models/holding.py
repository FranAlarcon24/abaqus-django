from django.db import models
from .asset import Asset
from .portfolio import Portfolio


class Holding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=30, decimal_places=10)

    def __str__(self):
        return f"{self.portfolio} - {self.asset}"
