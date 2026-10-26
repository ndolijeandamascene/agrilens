"""
AgriLens Seasonal Agricultural Surveys Views.
Presents active field survey campaigns, methodologies, and submission metrics with full CRUD management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Sum
from .models import SurveyCampaign, FarmSurveySubmission, DistrictSocioeconomicProfile
from .forms import SurveyCampaignForm, FarmSurveySubmissionForm
from apps.agriculture.models import AgriculturalSeason
from apps.data_management.models import ValidatedObservation


def survey_list(request):
    """Lists seasonal survey campaigns, SAS microdata coverage, and AHS 2024 socioeconomic profiles."""
    campaigns = SurveyCampaign.objects.select_related('season').annotate(
        submissions_count=Count('submissions')
    ).order_by('-season__year', '-season__season')

    seasons = AgriculturalSeason.objects.all().order_by('-year', '-season')

    # Query AHS 2024 Socioeconomic Profiles
    socio_profiles = DistrictSocioeconomicProfile.objects.select_related('district__province').order_by('district__province__name', 'district__name')
    
    # Calculate AHS National Benchmark Averages
    socio_stats = socio_profiles.aggregate(
        avg_extension=Avg('extension_advisory_reach_pct'),
        avg_twigire=Avg('twigire_muhinzi_membership_pct'),
        avg_credit=Avg('credit_access_pct'),
        avg_sacco=Avg('sacco_credit_share_pct'),
        avg_title=Avg('formal_land_title_pct'),
        avg_plots=Avg('avg_plots_per_household'),
        avg_sqm=Avg('avg_plot_area_sqm'),
        avg_sustainable=Avg('sustainable_practices_pct'),
        avg_dairy=Avg('dairy_producing_households_pct'),
        total_hh=Sum('sample_households_count'),
        total_parcels=Sum('total_plots_surveyed'),
    )

    # SAS validated microdata totals by season
    sas_season_counts = list(
        ValidatedObservation.objects.values('season__year', 'season__season')
        .annotate(plot_count=Count('id'))
        .order_by('-season__year', 'season__season')
    )
    total_sas_plots = ValidatedObservation.objects.count()

    active_tab = request.GET.get('tab', 'sas')

    context = {
        'page_title': 'National Agricultural Survey Intelligence (SAS & AHS)',
        'campaigns': campaigns,
        'seasons': seasons,
        'total_submissions': FarmSurveySubmission.objects.count(),
        'campaign_form': SurveyCampaignForm(),
        'socio_profiles': socio_profiles,
        'socio_stats': socio_stats,
        'sas_season_counts': sas_season_counts,
        'total_sas_plots': total_sas_plots,
        'active_tab': active_tab,
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


# ==============================================================================
# AHS DISTRICT SOCIOECONOMIC PROFILE CRUD
# ==============================================================================

@login_required
def socioeconomic_create(request):
    """Create a new AHS District Socioeconomic Profile."""
    from .forms import DistrictSocioeconomicProfileForm
    if request.method == 'POST':
        form = DistrictSocioeconomicProfileForm(request.POST)
        if form.is_valid():
            profile = form.save()
            messages.success(request, f"Socioeconomic profile for {profile.district.name} ({profile.survey_year}) created.")
            return redirect('/surveys/?tab=ahs')
        else:
            messages.error(request, "Failed to create profile. Please check the form errors.")
    else:
        form = DistrictSocioeconomicProfileForm()

    return render(request, 'surveys/socioeconomic_form.html', {
        'page_title': 'New District Socioeconomic Profile (AHS)',
        'form': form,
        'is_edit': False,
    })


@login_required
def socioeconomic_edit(request, pk):
    """Update an existing AHS District Socioeconomic Profile."""
    from .forms import DistrictSocioeconomicProfileForm
    profile = get_object_or_404(DistrictSocioeconomicProfile, pk=pk)
    if request.method == 'POST':
        form = DistrictSocioeconomicProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"Socioeconomic profile for {profile.district.name} updated.")
            return redirect('/surveys/?tab=ahs')
        else:
            messages.error(request, "Failed to update profile. Please check the form errors.")
    else:
        form = DistrictSocioeconomicProfileForm(instance=profile)

    return render(request, 'surveys/socioeconomic_form.html', {
        'page_title': f'Edit Socioeconomic Profile: {profile.district.name}',
        'form': form,
        'profile': profile,
        'is_edit': True,
    })


@login_required
def socioeconomic_delete(request, pk):
    """Delete a District Socioeconomic Profile."""
    profile = get_object_or_404(DistrictSocioeconomicProfile, pk=pk)
    if request.method == 'POST':
        dist_name = profile.district.name
        profile.delete()
        messages.success(request, f"Socioeconomic profile for {dist_name} deleted.")
    return redirect('/surveys/?tab=ahs')


# ==============================================================================
# FARM SURVEY SUBMISSION CRUD
# ==============================================================================

@login_required
def submission_create(request):
    """Submit a field questionnaire record."""
    if request.method == 'POST':
        form = FarmSurveySubmissionForm(request.POST)
        if form.is_valid():
            sub = form.save()
            messages.success(request, f"Survey submission #{sub.id} for {sub.crop.name} registered.")
            return redirect('surveys:survey_list')
        else:
            messages.error(request, "Failed to submit survey. Please review form inputs.")
    else:
        form = FarmSurveySubmissionForm()

    return render(request, 'surveys/submission_form.html', {
        'page_title': 'Register Survey Submission',
        'form': form,
        'is_edit': False,
    })


@login_required
def submission_edit(request, pk):
    """Edit an existing survey submission."""
    sub = get_object_or_404(FarmSurveySubmission, pk=pk)
    if request.method == 'POST':
        form = FarmSurveySubmissionForm(request.POST, instance=sub)
        if form.is_valid():
            form.save()
            messages.success(request, f"Survey submission #{sub.id} updated.")
            return redirect('surveys:survey_list')
        else:
            messages.error(request, "Failed to update submission.")
    else:
        form = FarmSurveySubmissionForm(instance=sub)

    return render(request, 'surveys/submission_form.html', {
        'page_title': f'Edit Submission #{sub.id}',
        'form': form,
        'submission': sub,
        'is_edit': True,
    })


@login_required
def submission_delete(request, pk):
    """Delete an individual survey questionnaire submission."""
    sub = get_object_or_404(FarmSurveySubmission, pk=pk)
    if request.method == 'POST':
        sub_id = sub.id
        sub.delete()
        messages.success(request, f"Survey submission #{sub_id} deleted.")
    return redirect('surveys:survey_list')

