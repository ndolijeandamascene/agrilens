"""
AgriLens Agricultural Inputs & Subsidy Tracking Views.
Catalogs certified seeds, chemical and organic fertilizers, and Smart Nkunganire subsidy price scales.
"""
from django.shortcuts import render
from .models import AgriculturalInput, InputCategory


def input_list(request):
    """Lists agricultural inputs and subsidy price benchmarks."""
    category_id = request.GET.get('category')

    inputs = AgriculturalInput.objects.select_related('category').all().order_by('category__name', 'name')
    if category_id and category_id.isdigit():
        inputs = inputs.filter(category_id=int(category_id))

    categories = InputCategory.objects.all().order_by('name')

    context = {
        'page_title': 'Agricultural Inputs & Subsidy Price Scales',
        'inputs': inputs,
        'categories': categories,
        'selected_category': category_id,
        'total_inputs': AgriculturalInput.objects.count(),
    }
    return render(request, 'inputs/input_list.html', context)

