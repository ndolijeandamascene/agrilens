"""
AgriLens Farmer Profiles & Cooperatives Views.
Demographic tracking, household land holdings, and agricultural cooperative networks.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from .models import Farmer, Cooperative
from .forms import CooperativeForm, FarmerForm


def farmer_list(request):
    """Lists registered agricultural cooperatives and farmers with CRUD actions."""
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
        'coop_form': CooperativeForm(),
        'farmer_form': FarmerForm(),
    }
    return render(request, 'farmers/farmer_list.html', context)


@login_required
def cooperative_create(request):
    """Register a new agricultural cooperative."""
    if request.method == 'POST':
        form = CooperativeForm(request.POST)
        if form.is_valid():
            coop = form.save()
            messages.success(request, f"Cooperative '{coop.name}' successfully registered.")
            return redirect('farmers:farmer_list')
        else:
            messages.error(request, "Failed to register cooperative. Please check the form errors.")
    else:
        form = CooperativeForm()

    return render(request, 'farmers/cooperative_form.html', {
        'page_title': 'Register Agricultural Cooperative',
        'form': form,
        'is_edit': False,
    })


@login_required
def cooperative_edit(request, pk):
    """Update details of an existing cooperative."""
    coop = get_object_or_404(Cooperative, pk=pk)
    if request.method == 'POST':
        form = CooperativeForm(request.POST, instance=coop)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cooperative '{coop.name}' updated successfully.")
            return redirect('farmers:farmer_list')
    else:
        form = CooperativeForm(instance=coop)

    return render(request, 'farmers/cooperative_form.html', {
        'page_title': f'Edit Cooperative: {coop.name}',
        'form': form,
        'coop': coop,
        'is_edit': True,
    })


@login_required
def cooperative_delete(request, pk):
    """Delete a cooperative if no members or surveys are attached."""
    coop = get_object_or_404(Cooperative, pk=pk)
    if request.method == 'POST':
        name = coop.name
        member_count = coop.members.count()
        if member_count > 0:
            messages.warning(request, f"Cannot delete '{name}' because it has {member_count} registered members.")
        else:
            coop.delete()
            messages.success(request, f"Cooperative '{name}' has been deleted.")
    return redirect('farmers:farmer_list')


@login_required
def farmer_create(request):
    """Register a new smallholder farmer."""
    if request.method == 'POST':
        form = FarmerForm(request.POST)
        if form.is_valid():
            farmer = form.save()
            messages.success(request, f"Farmer '{farmer}' registered successfully.")
            return redirect('farmers:farmer_list')
        else:
            messages.error(request, "Failed to register farmer. Please verify input fields.")
    else:
        form = FarmerForm()

    return render(request, 'farmers/farmer_form.html', {
        'page_title': 'Register Smallholder Farmer',
        'form': form,
        'is_edit': False,
    })


@login_required
def farmer_edit(request, pk):
    """Update an existing farmer record."""
    farmer = get_object_or_404(Farmer, pk=pk)
    if request.method == 'POST':
        form = FarmerForm(request.POST, instance=farmer)
        if form.is_valid():
            form.save()
            messages.success(request, f"Farmer '{farmer}' updated successfully.")
            return redirect('farmers:farmer_list')
    else:
        form = FarmerForm(instance=farmer)

    return render(request, 'farmers/farmer_form.html', {
        'page_title': f'Edit Farmer: {farmer}',
        'form': form,
        'farmer': farmer,
        'is_edit': True,
    })


@login_required
def farmer_delete(request, pk):
    """Delete a farmer profile."""
    farmer = get_object_or_404(Farmer, pk=pk)
    if request.method == 'POST':
        name = str(farmer)
        farmer.delete()
        messages.success(request, f"Farmer profile '{name}' has been deleted.")
    return redirect('farmers:farmer_list')
