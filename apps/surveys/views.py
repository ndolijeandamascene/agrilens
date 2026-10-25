"""
AgriLens Seasonal Agricultural Surveys Views.
Presents active field survey campaigns, methodologies, and submission metrics with full CRUD management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import SurveyCampaign, FarmSurveySubmission
from .forms import SurveyCampaignForm, FarmSurveySubmissionForm
from apps.agriculture.models import AgriculturalSeason


def survey_list(request):
    """Lists seasonal survey campaigns and microdata coverage."""
    campaigns = SurveyCampaign.objects.select_related('season').annotate(
        submissions_count=Count('submissions')
    ).order_by('-season__year', '-season__season')

    seasons = AgriculturalSeason.objects.all().order_by('-year', '-season')

    context = {
        'page_title': 'Seasonal Agricultural Surveys (SAS) Monitoring',
        'campaigns': campaigns,
        'seasons': seasons,
        'total_submissions': FarmSurveySubmission.objects.count(),
        'campaign_form': SurveyCampaignForm(),
    }
    return render(request, 'surveys/survey_list.html', context)


@login_required
def survey_campaign_create(request):
    """Initialize a new seasonal survey campaign."""
    if request.method == 'POST':
        form = SurveyCampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save()
            messages.success(request, f"Survey campaign '{campaign.title}' initialized.")
            return redirect('surveys:survey_list')
        else:
            messages.error(request, "Failed to create survey campaign. Please check input values.")
    else:
        form = SurveyCampaignForm()

    return render(request, 'surveys/campaign_form.html', {
        'page_title': 'Initialize Seasonal Survey Campaign',
        'form': form,
        'is_edit': False,
    })


@login_required
def survey_campaign_edit(request, pk):
    """Update survey campaign parameters."""
    campaign = get_object_or_404(SurveyCampaign, pk=pk)
    if request.method == 'POST':
        form = SurveyCampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            messages.success(request, f"Survey campaign '{campaign.title}' updated.")
            return redirect('surveys:survey_list')
    else:
        form = SurveyCampaignForm(instance=campaign)

    return render(request, 'surveys/campaign_form.html', {
        'page_title': f'Edit Campaign: {campaign.title}',
        'form': form,
        'campaign': campaign,
        'is_edit': True,
    })


@login_required
def survey_campaign_delete(request, pk):
    """Delete a survey campaign if no submissions attached."""
    campaign = get_object_or_404(SurveyCampaign, pk=pk)
    if request.method == 'POST':
        title = campaign.title
        sub_count = campaign.submissions.count()
        if sub_count > 0:
            messages.warning(request, f"Cannot delete '{title}' because {sub_count} field survey submissions are attached.")
        else:
            campaign.delete()
            messages.success(request, f"Survey campaign '{title}' deleted.")
    return redirect('surveys:survey_list')
