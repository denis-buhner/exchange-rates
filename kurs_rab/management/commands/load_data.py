import pandas as pd
from django.core.management.base import BaseCommand
from kurs_rab.models import CurrencyData
from datetime import datetime

class Command(BaseCommand):
    help = 'Загрузка данных из CSV в базу данных'

    def handle(self, *args, **options):
        # 1. Читаем файл (укажи правильный путь к своему файлу)
        file_path = 'D:\kr\kr\data_182.csv' 
        df = pd.read_csv(file_path, sep=';')

        # 2. Очистка данных (убираем пустые letter_code, если они не нужны)
        df = df.dropna(subset=['letter_code'])

        # 3. Подготовка списка объектов
        entries = []
        for index, row in df.iterrows():
            # Превращаем строку даты в объект даты Python
            # Проверь формат! Если в файле 2021-01-01, то это '%Y-%m-%d'
            date_obj = pd.to_datetime(row['date']).date()

            entries.append(
                CurrencyData(
                    date=date_obj,
                    currency=row['currency'],
                    letter_code=row['letter_code'],
                    rate=row['rate']
                )
            )

            # Чтобы не переполнять память, сохраняем порциями по 5000 строк
            if len(entries) > 5000:
                CurrencyData.objects.bulk_create(entries)
                entries = []
                self.stdout.write(f"Загружено {index} строк...")

        # Догружаем остаток
        if entries:
            CurrencyData.objects.bulk_create(entries)
            
        self.stdout.write(self.style.SUCCESS('Данные успешно загружены!'))