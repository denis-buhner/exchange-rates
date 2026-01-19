from django.db import models

class CurrencyData(models.Model):
    date = models.DateField()               # Для колонки date
    currency = models.CharField(max_length=255) # Название валюты
    letter_code = models.CharField(max_length=10, null=True) # USD, EUR и т.д.
    rate = models.FloatField()               # Для курса

    def __str__(self):
        return f"{self.letter_code} on {self.date}"