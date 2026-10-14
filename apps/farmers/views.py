"""
AgriLens Farmer Profiles & Cooperatives Views.
Demographic tracking, household land holdings, and agricultural cooperative networks.
"""
from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Count
from .models import Farmer, Cooperative


def farmer_list(request):
    """Lists registered agricultural cooperatives and farmers."""
    cooperatives = Cooperative.objects.select_related('sector__district').annotate(
        members_count=Count('members')
    ).order_by('name')

    farmers = Farmer.objects.select_related('cooperative', 'sector__district').order_by('last_name', 'first_name')
    paginator = Paginator(farmers, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_title': 'Farmers & Agricultural Cooperatives Registry',
        'cooperatives': cooperatives,
        'page_obj': page_obj,
        'total_farmers': Farmer.objects.count(),
        'total_cooperatives': Cooperative.objects.count(),
    }
    return render(request, 'farmers/farmer_list.html', context)

