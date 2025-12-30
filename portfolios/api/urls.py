from django.urls import path
from .views import portfolio_history

urlpatterns = [
    path("portfolio/history/", portfolio_history),
]
