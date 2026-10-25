"""
AgriLens Agriculture Domain Views.
Displays priority and food security crops, classification categories,
and seasonal agricultural calendars with full CRUD capabilities.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Crop, CropCategory, AgriculturalSeason
from .forms import CropForm, CropCategoryForm
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

    categories = CropCategory.objects.annotate(crops_count=Count('crops')).order_by('name')
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


@login_required
def crop_create(request):
    """Register a new crop in the national taxonomy."""
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save()
            messages.success(request, f"Crop '{crop.name}' registered successfully.")
            return redirect('agriculture:crop_detail', pk=crop.pk)
        else:
            messages.error(request, "Failed to register crop. Please check form validation errors.")
    else:
        form = CropForm()

    return render(request, 'agriculture/crop_form.html', {
        'page_title': 'Register New Crop Taxonomy Entry',
        'form': form,
        'is_edit': False,
    })


@login_required
def crop_edit(request, pk):
    """Update taxonomy and agronomic attributes of a crop."""
    crop = get_object_or_404(Crop, pk=pk)
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            form.save()
            messages.success(request, f"Crop '{crop.name}' updated successfully.")
            return redirect('agriculture:crop_detail', pk=crop.pk)
    else:
        form = CropForm(instance=crop)

    return render(request, 'agriculture/crop_form.html', {
        'page_title': f'Edit Crop: {crop.name}',
        'form': form,
        'crop': crop,
        'is_edit': True,
    })


@login_required
def crop_delete(request, pk):
    """Delete a crop record if no validated observations depend on it."""
    crop = get_object_or_404(Crop, pk=pk)
    if request.method == 'POST':
        name = crop.name
        obs_count = ValidatedObservation.objects.filter(crop=crop).count()
        if obs_count > 0:
            messages.warning(request, f"Cannot delete '{name}' because {obs_count} validated survey observations depend on it.")
            return redirect('agriculture:crop_detail', pk=crop.pk)
        
        crop.delete()
        messages.success(request, f"Crop '{name}' deleted successfully.")
        return redirect('agriculture:crop_list')

    return redirect('agriculture:crop_list')


@login_required
def category_create(request):
    """Register a new crop category."""
    if request.method == 'POST':
        form = CropCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Crop category '{cat.name}' created.")
            return redirect('agriculture:crop_list')
        else:
            messages.error(request, "Failed to create crop category.")
    else:
        form = CropCategoryForm()

    return render(request, 'agriculture/category_form.html', {
        'page_title': 'Add Crop Category',
        'form': form,
        'is_edit': False,
    })


@login_required
def category_edit(request, pk):
    """Update a crop category."""
    cat = get_object_or_404(CropCategory, pk=pk)
    if request.method == 'POST':
        form = CropCategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{cat.name}' updated.")
            return redirect('agriculture:crop_list')
    else:
        form = CropCategoryForm(instance=cat)

    return render(request, 'agriculture/category_form.html', {
        'page_title': f'Edit Crop Category: {cat.name}',
        'form': form,
        'cat': cat,
        'is_edit': True,
    })


@login_required
def category_delete(request, pk):
    """Delete a crop category if no crops belong to it."""
    cat = get_object_or_404(CropCategory, pk=pk)
    if request.method == 'POST':
        name = cat.name
        crops_count = cat.crops.count()
        if crops_count > 0:
            messages.warning(request, f"Cannot delete '{name}' because it contains {crops_count} assigned crops.")
        else:
            cat.delete()
            messages.success(request, f"Crop category '{name}' deleted.")
    return redirect('agriculture:crop_list')
