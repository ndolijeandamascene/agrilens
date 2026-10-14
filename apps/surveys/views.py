"""
AgriLens Seasonal Agricultural Surveys Views.
Presents active field survey campaigns, methodologies, and submission metrics.
"""
from django.shortcuts import render
from django.db.models import Count
from .models import SurveyCampaign, FarmSurveySubmission
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
    }
    return render(request, 'surveys/survey_list.html', context)

