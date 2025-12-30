from django.db import models


class Portfolio(models.Model):
    name = models.CharField(max_length=50)
    initial_value = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return self.name
