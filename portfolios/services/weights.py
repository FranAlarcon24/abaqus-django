import pandas as pd
from decimal import Decimal

from portfolios.models import Asset, Portfolio, Price, Holding


def normalize_name(value: str) -> str:
    return value.strip()


def create_initial_holdings_from_excel(path: str):
    df = pd.read_excel(path, sheet_name="weights")

    # Fecha t=0 (primer precio disponible)
    first_price_date = (
        Price.objects.order_by("date")
        .values_list("date", flat=True)
        .first()
    )

    prices_t0 = {
        normalize_name(p.asset.name): p.price
        for p in Price.objects.filter(date=first_price_date)
    }

    portfolio_1 = Portfolio.objects.get(name="Portfolio 1")
    portfolio_2 = Portfolio.objects.get(name="Portfolio 2")

    for _, row in df.iterrows():
        asset_name = normalize_name(str(row.iloc[1]))
        weight_p1 = Decimal(row.iloc[2])
        weight_p2 = Decimal(row.iloc[3])

        asset = Asset.objects.get(name=asset_name)
        price_t0 = prices_t0[asset_name]

        qty_1 = (portfolio_1.initial_value * weight_p1) / price_t0
        qty_2 = (portfolio_2.initial_value * weight_p2) / price_t0

        Holding.objects.update_or_create(
            portfolio=portfolio_1,
            asset=asset,
            defaults={"quantity": qty_1},
        )

        Holding.objects.update_or_create(
            portfolio=portfolio_2,
            asset=asset,
            defaults={"quantity": qty_2},
        )
