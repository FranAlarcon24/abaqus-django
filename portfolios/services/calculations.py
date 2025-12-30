from decimal import Decimal
from portfolios.models import Holding, Price


def portfolio_snapshot(portfolio, date):
    """
    Calcula x_i,t , w_i,t y V_t para un portfolio en una fecha dada.
    """
    holdings = Holding.objects.filter(portfolio=portfolio)

    positions = []
    total_value = Decimal("0")

    for holding in holdings:
        price = Price.objects.get(
            asset=holding.asset,
            date=date,
        ).price

        xi = holding.quantity * price
        total_value += xi

        positions.append(
            {
                "asset": holding.asset.name,
                "xi": xi,
            }
        )

    for p in positions:
        p["weight"] = p["xi"] / total_value if total_value > 0 else Decimal("0")

    return {
        "date": date,
        "Vt": total_value,
        "positions": positions,
    }
