from django.contrib import admin
from .models import SurveyCampaign, FarmSurveySubmission, DistrictSocioeconomicProfile

admin.site.register(SurveyCampaign)
admin.site.register(FarmSurveySubmission)
admin.site.register(DistrictSocioeconomicProfile)
