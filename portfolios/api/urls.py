from django.urls import path
from .views import (
    portfolio_history,
    portfolio_value,
    portfolio_performance_ytd,
    positions,
    cash_balance,
    assets_list,
    assets_search,
    asset_market_data,
)

urlpatterns = [
    path("portfolio/history/", portfolio_history, name="portfolio-history"),
    path("portfolios/value/", portfolio_value, name="portfolio-value"),
    path("portfolios/performance/ytd/", portfolio_performance_ytd, name="portfolio-performance-ytd"),
    path("portfolios/positions/", positions, name="portfolio-positions"),
    path("accounts/cash-balance/", cash_balance, name="cash-balance"),
    path("assets/", assets_list, name="assets-list"),
    path("assets/search/", assets_search, name="assets-search"),
    path("assets/<str:asset_name>/market-data/", asset_market_data, name="asset-market-data"),
]
