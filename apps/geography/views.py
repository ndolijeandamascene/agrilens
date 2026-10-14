"""
AgriLens Geography Domain Views.
Displays Rwanda's administrative structure: 5 Provinces, 30 Districts, 416 Sectors.
"""
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from .models import Province, District, Sector
from apps.data_management.models import ValidatedObservation
from apps.accounts.permissions import can_access_district, scope_queryset_by_geography


def district_list(request):
    """Lists Rwanda's administrative districts with provinces and sector counts (scoped for District Officers)."""
    province_id = request.GET.get('province')

    provinces = Province.objects.prefetch_related('districts').all().order_by('name')
    districts = District.objects.select_related('province').annotate(
        sectors_count=Count('sectors', distinct=True),
        observations_count=Count('observations', distinct=True)
    ).order_by('province__name', 'name')

    # Geographic scoping for District Officers
    districts = scope_queryset_by_geography(districts, request.user, district_field='id')

    if province_id and province_id.isdigit():
        districts = districts.filter(province_id=int(province_id))

    context = {
        'page_title': 'Administrative Geography & District Coverage',
        'provinces': provinces,
        'districts': districts,
        'selected_province': province_id,
        'total_districts': districts.count(),
        'total_sectors': Sector.objects.count(),
    }
    return render(request, 'geography/district_list.html', context)


def district_detail(request, pk):
    """Detailed view for an individual district with sectors and observations, with geographic clearance checks."""
    district = get_object_or_404(District.objects.select_related('province'), pk=pk)

    # Server-side Geographic Clearance Enforcement
    if not can_access_district(request.user, district.id):
        return render(request, '403.html', {
            'reason': f"Geographic Access Restricted: You are not authorized to inspect intelligence for {district.name} District."
        }, status=403)

    sectors = Sector.objects.filter(district=district).order_by('name')
    recent_obs = ValidatedObservation.objects.filter(district=district).select_related(
        'crop', 'season'
    ).order_by('-id')[:10]

    context = {
        'page_title': f"{district.name} District &bull; Geographic Intelligence",
        'district': district,
        'sectors': sectors,
        'recent_obs': recent_obs,
        'total_obs': ValidatedObservation.objects.filter(district=district).count(),
    }
    return render(request, 'geography/district_detail.html', context)

