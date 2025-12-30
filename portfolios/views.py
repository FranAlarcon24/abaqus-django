from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def home(request):
    return JsonResponse(
        {
            "message": "Portfolio API running",
            "endpoints": {
                "admin": "/admin/",
                "portfolio_history": "/api/portfolio/history/"
            }
        }
    )
