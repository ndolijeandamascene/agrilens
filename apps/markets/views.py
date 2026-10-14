"""
AgriLens Commodity Markets Views.
Monitors weekly wholesale and retail commodity prices across major commercial hubs.
"""
from django.shortcuts import render
from django.core.paginator import Paginator
from apps.markets.models import CommodityPrice, MarketLocation
from apps.agriculture.models import Crop


def market_list(request):
    """Lists commodity price surveillance records across markets with crop filters."""
    crop_filter = request.GET.get('crop', '')
    market_filter = request.GET.get('market', '')

    prices = CommodityPrice.objects.select_related('market__district', 'crop').order_by('-date_recorded')

    if crop_filter:
        prices = prices.filter(crop__name__iexact=crop_filter)

    if market_filter and market_filter.isdigit():
        prices = prices.filter(market_id=int(market_filter))

    paginator = Paginator(prices, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    priority_crops = Crop.objects.filter(is_priority_crop=True).order_by('name')
    markets = MarketLocation.objects.select_related('district').all().order_by('name')

    context = {
        'page_title': 'Commodity Price Surveillance & Market Hubs',
        'page_obj': page_obj,
        'priority_crops': priority_crops,
        'markets': markets,
        'selected_crop': crop_filter,
        'selected_market': market_filter,
        'total_prices_count': CommodityPrice.objects.count(),
    }
    return render(request, 'markets/market_list.html', context)

