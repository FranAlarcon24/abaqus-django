from datetime import datetime, date
from decimal import Decimal

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db.models import Max, Sum

from portfolios.models import Portfolio, Price, Asset, Holding
from portfolios.services.calculations import portfolio_snapshot


@require_GET
def portfolio_history(request):
    # Usuario (si usas middleware de Firebase)
    firebase_user = getattr(request, "firebase_user", {})
    user_email = firebase_user.get("email")

    # Parámetros GET
    portfolio_name = request.GET.get("portfolio")
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if not all([portfolio_name, fecha_inicio, fecha_fin]):
        return JsonResponse(
            {"error": "portfolio, fecha_inicio y fecha_fin son requeridos"},
            status=400,
        )

    # Buscar portfolio
    try:
        portfolio = Portfolio.objects.get(name=portfolio_name)
    except Portfolio.DoesNotExist:
        return JsonResponse(
            {"error": "Portfolio no encontrado"},
            status=404,
        )

    # Parsear fechas
    try:
        start = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        end = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse(
            {"error": "Formato de fecha inválido. Use YYYY-MM-DD"},
            status=400,
        )

    # Fechas disponibles en precios
    dates = (
        Price.objects.filter(date__range=(start, end))
        .values_list("date", flat=True)
        .distinct()
        .order_by("date")
    )

    # Snapshot por fecha
    data = [
        portfolio_snapshot(portfolio, date)
        for date in dates
    ]

    return JsonResponse(
        {
            "user": user_email,
            "portfolio": portfolio_name,
            "from": fecha_inicio,
            "to": fecha_fin,
            "data": data,
        },
        safe=False,
    )


@require_GET
def portfolio_value(request):
    """Total value across all portfolios using the latest available prices."""
    # Latest price date per asset
    latest_dates = (
        Price.objects.values("asset").annotate(latest=Max("date"))
    )

    # Build a map asset_id -> latest_date
    latest_map = {row["asset"]: row["latest"] for row in latest_dates}

    total = Decimal("0")
    for h in Holding.objects.all():
        latest = latest_map.get(h.asset_id)
        if latest is None:
            continue
        price = (
            Price.objects.filter(asset=h.asset, date=latest)
            .values_list("price", flat=True)
            .first()
        )
        if price is None:
            continue
        total += h.quantity * price

    return JsonResponse({"total_value": float(total)})


@require_GET
def portfolio_performance_ytd(request):
    """Simple YTD performance: series of total portfolio value by date in year."""
    today = date.today()
    start = date(today.year, 1, 1)

    # Distinct dates in current year
    dates = (
        Price.objects.filter(date__range=(start, today))
        .values_list("date", flat=True)
        .distinct()
        .order_by("date")
    )

    series = []
    for d in dates:
        vt = Decimal("0")
        # For each holding, pick price for the same date
        for h in Holding.objects.all():
            price = (
                Price.objects.filter(asset=h.asset, date=d)
                .values_list("price", flat=True)
                .first()
            )
            if price is None:
                continue
            vt += h.quantity * price
        series.append({"date": d.isoformat(), "total_value": float(vt)})

    # Basic percent change YTD if we have at least two points
    ytd_pct = None
    if len(series) >= 2 and series[0]["total_value"]:
        ytd_pct = (series[-1]["total_value"] / series[0]["total_value"] - 1) * 100.0

    return JsonResponse({"points": series, "ytd_return_pct": ytd_pct})


@require_GET
def positions(request):
    """Return current positions with latest price and market value."""
    latest_dates = (
        Price.objects.values("asset").annotate(latest=Max("date"))
    )
    latest_map = {row["asset"]: row["latest"] for row in latest_dates}

    items = []
    for h in Holding.objects.select_related("asset", "portfolio"):
        latest = latest_map.get(h.asset_id)
        price = None
        if latest is not None:
            price = (
                Price.objects.filter(asset=h.asset, date=latest)
                .values_list("price", flat=True)
                .first()
            )
        market_value = float(h.quantity * price) if price is not None else 0.0
        items.append(
            {
                "portfolio": h.portfolio.name,
                "name": h.asset.name,
                "quantity": float(h.quantity),
                "last_price": float(price) if price is not None else None,
                "market_value": market_value,
            }
        )

    return JsonResponse(items, safe=False)


@require_GET
def cash_balance(request):
    """Compute cash using holding of asset named 'MM/Caja' if present."""
    try:
        cash_asset = Asset.objects.get(name__iexact="MM/Caja")
    except Asset.DoesNotExist:
        return JsonResponse({"cash_balance": 0.0})

    latest = (
        Price.objects.filter(asset=cash_asset).aggregate(latest=Max("date"))
    )["latest"]
    if latest is None:
        return JsonResponse({"cash_balance": 0.0})

    price = (
        Price.objects.filter(asset=cash_asset, date=latest)
        .values_list("price", flat=True)
        .first()
    )
    qty = (
        Holding.objects.filter(asset=cash_asset)
        .aggregate(q=Sum("quantity"))
        .get("q")
    )
    if qty is None or price is None:
        return JsonResponse({"cash_balance": 0.0})

    return JsonResponse({"cash_balance": float(qty * price)})


# --- Assets endpoints used by Search page ---

@require_GET
def assets_list(request):
    """List all assets with optional last price."""
    assets = Asset.objects.all().order_by("name")
    results = []
    # Precompute latest price per asset
    latest_map = {
        row["asset"]: row["latest"]
        for row in Price.objects.values("asset").annotate(latest=Max("date"))
    }
    for a in assets:
        latest = latest_map.get(a.id)
        last_price = None
        prev_price = None
        if latest:
            last_price = (
                Price.objects.filter(asset=a, date=latest)
                .values_list("price", flat=True)
                .first()
            )
            prev_price = (
                Price.objects.filter(asset=a, date__lt=latest).order_by("-date")
                .values_list("price", flat=True)
                .first()
            )
        change_abs = None
        change_pct = None
        if last_price is not None and prev_price is not None:
            try:
                change_abs = float(last_price) - float(prev_price)
                base = float(prev_price) or 0.0
                change_pct = ((float(last_price) / base) - 1.0) * 100.0 if base != 0.0 else None
            except Exception:
                change_abs = None
                change_pct = None
        results.append({
            "name": a.name,
            "last_price": float(last_price) if last_price is not None else None,
            "change_abs": change_abs,
            "change_pct": change_pct,
        })
    return JsonResponse({"results": results})


@require_GET
def assets_search(request):
    q = request.GET.get("query", "").strip()
    if not q:
        return assets_list(request)
    qs = Asset.objects.filter(name__icontains=q).order_by("name")
    latest_map = {
        row["asset"]: row["latest"]
        for row in Price.objects.values("asset").annotate(latest=Max("date"))
    }
    results = []
    for a in qs:
        latest = latest_map.get(a.id)
        last_price = None
        prev_price = None
        if latest:
            last_price = (
                Price.objects.filter(asset=a, date=latest)
                .values_list("price", flat=True)
                .first()
            )
            prev_price = (
                Price.objects.filter(asset=a, date__lt=latest).order_by("-date")
                .values_list("price", flat=True)
                .first()
            )
        change_abs = None
        change_pct = None
        if last_price is not None and prev_price is not None:
            try:
                change_abs = float(last_price) - float(prev_price)
                base = float(prev_price) or 0.0
                change_pct = ((float(last_price) / base) - 1.0) * 100.0 if base != 0.0 else None
            except Exception:
                change_abs = None
                change_pct = None
        results.append({
            "name": a.name,
            "last_price": float(last_price) if last_price is not None else None,
            "change_abs": change_abs,
            "change_pct": change_pct,
        })
    return JsonResponse({"results": results})


@require_GET
def asset_market_data(request, asset_name: str):
    """Return latest price and simple change using previous date if available."""
    try:
        asset = Asset.objects.get(name=asset_name)
    except Asset.DoesNotExist:
        return JsonResponse({"error": "Asset no encontrado"}, status=404)

    latest = (
        Price.objects.filter(asset=asset).aggregate(latest=Max("date"))
    )["latest"]
    if latest is None:
        return JsonResponse({"name": asset.name, "last_price": None, "change_pct": None})

    last_price = (
        Price.objects.filter(asset=asset, date=latest)
        .values_list("price", flat=True)
        .first()
    )
    prev = (
        Price.objects.filter(asset=asset, date__lt=latest).order_by("-date")
        .values_list("price", flat=True)
        .first()
    )
    change_pct = None
    if prev:
        try:
            change_pct = (float(last_price) / float(prev) - 1.0) * 100.0
        except Exception:
            change_pct = None

    return JsonResponse({
        "name": asset.name,
        "last_price": float(last_price) if last_price is not None else None,
        "change_pct": change_pct,
    })
