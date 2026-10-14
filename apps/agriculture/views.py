"""
AgriLens Agriculture Domain Views.
Displays priority and food security crops, classification categories,
and seasonal agricultural calendars.
"""
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Crop, CropCategory, AgriculturalSeason
from apps.data_management.models import ValidatedObservation


def crop_list(request):
    """Lists priority and staple crops with search and category filters."""
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    is_priority = request.GET.get('priority')

    crops = Crop.objects.select_related('category').annotate(
        observations_count=Count('observations')
    ).order_by('-is_priority_crop', 'name')

    if query:
        crops = crops.filter(
            Q(name__icontains=query) |
            Q(kinyarwanda_name__icontains=query) |
            Q(scientific_name__icontains=query)
        )

    if category_id and category_id.isdigit():
        crops = crops.filter(category_id=int(category_id))

    if is_priority == '1':
        crops = crops.filter(is_priority_crop=True)

    paginator = Paginator(crops, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = CropCategory.objects.all().order_by('name')
    seasons = AgriculturalSeason.objects.all().order_by('-year', '-season')

    context = {
        'page_title': 'Crops & Agricultural Seasons Registry',
        'page_obj': page_obj,
        'categories': categories,
        'seasons': seasons,
        'selected_category': category_id,
        'selected_priority': is_priority,
        'query': query,
        'total_crops_count': Crop.objects.count(),
        'priority_count': Crop.objects.filter(is_priority_crop=True).count(),
    }
    return render(request, 'agriculture/crop_list.html', context)


def crop_detail(request, pk):
    """Detailed view for an individual crop with observations summary."""
    crop = get_object_or_404(Crop.objects.select_related('category'), pk=pk)
    recent_obs = ValidatedObservation.objects.filter(crop=crop).select_related(
        'district', 'season'
    ).order_by('-id')[:10]

    context = {
        'page_title': f"{crop.name} &bull; Crop Specifications",
        'crop': crop,
        'recent_obs': recent_obs,
        'total_obs': ValidatedObservation.objects.filter(crop=crop).count(),
    }
    return render(request, 'agriculture/crop_detail.html', context)

