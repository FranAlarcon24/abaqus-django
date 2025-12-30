from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from portfolios.models import Portfolio, Price
from portfolios.services.calculations import portfolio_snapshot


@require_GET
def portfolio_history(request):
    # 🔐 Usuario Firebase inyectado por el middleware
    firebase_user = request.firebase_user
    user_email = firebase_user.get("email")

    portfolio_name = request.GET.get("portfolio")
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")

    if not all([portfolio_name, fecha_inicio, fecha_fin]):
        return JsonResponse(
            {"error": "portfolio, fecha_inicio y fecha_fin son requeridos"},
            status=400,
        )

    try:
        portfolio = Portfolio.objects.get(name=portfolio_name)
    except Portfolio.DoesNotExist:
        return JsonResponse(
            {"error": "Portfolio no encontrado"},
            status=404,
        )

    start = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    end = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    dates = (
        Price.objects.filter(date__range=(start, end))
        .values_list("date", flat=True)
        .distinct()
        .order_by("date")
    )

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
