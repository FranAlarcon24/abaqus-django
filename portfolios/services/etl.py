import pandas as pd
from decimal import Decimal
from portfolios.models import Asset, Price


def load_prices_from_excel(path: str):
    """
    Lee el sheet 'Precios' del Excel y carga Assets y Prices.
    """
    df = pd.read_excel(path, sheet_name="Precios")

    date_column = df.columns[0]
    asset_columns = df.columns[1:]

    assets = {}
    for col in asset_columns:
        asset, _ = Asset.objects.get_or_create(name=col)
        assets[col] = asset

    prices_created = 0

    for _, row in df.iterrows():
        date = row[date_column]

        for col in asset_columns:
            value = row[col]

            if pd.isna(value):
                continue

            Price.objects.update_or_create(
                asset=assets[col],
                date=date,
                defaults={"price": Decimal(value)},
            )
            prices_created += 1

    return prices_created
