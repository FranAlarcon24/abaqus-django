from django.db import models
from .asset import Asset


class Price(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    price = models.DecimalField(max_digits=20, decimal_places=6)

    class Meta:
        unique_together = ("asset", "date")

    def __str__(self):
        return f"{self.asset} - {self.date}"
