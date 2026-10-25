"""
AgriLens Agricultural Inputs & Subsidy Tracking Views.
Catalogs certified seeds, chemical and organic fertilizers, and Smart Nkunganire subsidy price scales.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AgriculturalInput, InputCategory
from .forms import AgriculturalInputForm, InputCategoryForm


def input_list(request):
    """Lists agricultural inputs and subsidy price benchmarks with CRUD management."""
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
        'input_form': AgriculturalInputForm(),
        'category_form': InputCategoryForm(),
    }
    return render(request, 'inputs/input_list.html', context)


@login_required
def input_create(request):
    """Register a new agricultural input item."""
    if request.method == 'POST':
        form = AgriculturalInputForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f"Agricultural input '{item.name}' added successfully.")
            return redirect('inputs:input_list')
        else:
            messages.error(request, "Failed to create input. Please check input errors.")
    else:
        form = AgriculturalInputForm()

    return render(request, 'inputs/input_form.html', {
        'page_title': 'Add Agricultural Input Benchmark',
        'form': form,
        'is_edit': False,
    })


@login_required
def input_edit(request, pk):
    """Update an existing agricultural input benchmark."""
    item = get_object_or_404(AgriculturalInput, pk=pk)
    if request.method == 'POST':
        form = AgriculturalInputForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f"Input benchmark '{item.name}' updated successfully.")
            return redirect('inputs:input_list')
    else:
        form = AgriculturalInputForm(instance=item)

    return render(request, 'inputs/input_form.html', {
        'page_title': f'Edit Input: {item.name}',
        'form': form,
        'item': item,
        'is_edit': True,
    })


@login_required
def input_delete(request, pk):
    """Delete an agricultural input benchmark."""
    item = get_object_or_404(AgriculturalInput, pk=pk)
    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f"Agricultural input '{name}' has been deleted.")
    return redirect('inputs:input_list')


@login_required
def category_create(request):
    """Register a new input category."""
    if request.method == 'POST':
        form = InputCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Input category '{cat.name}' created.")
            return redirect('inputs:input_list')
        else:
            messages.error(request, "Failed to create input category.")
    else:
        form = InputCategoryForm()

    return render(request, 'inputs/category_form.html', {
        'page_title': 'Add Input Category',
        'form': form,
        'is_edit': False,
    })


@login_required
def category_edit(request, pk):
    """Update an input category."""
    cat = get_object_or_404(InputCategory, pk=pk)
    if request.method == 'POST':
        form = InputCategoryForm(request.POST, instance=cat)
        if form.is_valid():
            form.save()
            messages.success(request, f"Category '{cat.name}' updated successfully.")
            return redirect('inputs:input_list')
    else:
        form = InputCategoryForm(instance=cat)

    return render(request, 'inputs/category_form.html', {
        'page_title': f'Edit Category: {cat.name}',
        'form': form,
        'cat': cat,
        'is_edit': True,
    })


@login_required
def category_delete(request, pk):
    """Delete an input category if no items belong to it."""
    cat = get_object_or_404(InputCategory, pk=pk)
    if request.method == 'POST':
        name = cat.name
        items_count = cat.items.count()
        if items_count > 0:
            messages.warning(request, f"Cannot delete '{name}' because it contains {items_count} catalog items.")
        else:
            cat.delete()
            messages.success(request, f"Input category '{name}' deleted.")
    return redirect('inputs:input_list')
