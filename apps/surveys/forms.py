from django import forms
from .models import SurveyCampaign, FarmSurveySubmission, DistrictSocioeconomicProfile


class SurveyCampaignForm(forms.ModelForm):
    """Survey Campaign setup and update form."""
    class Meta:
        model = SurveyCampaign
        fields = ['title', 'season', 'is_active', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Seasonal Agricultural Survey 2025 Season A', 'required': True}),
            'season': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'is_active': forms.CheckboxInput(attrs={'style': 'width: 18px; height: 18px; cursor: pointer;'}),
            'description': forms.Textarea(attrs={'class': 'dash-textarea-input', 'rows': 3, 'placeholder': 'Sampling methodology, survey scope, enumeration timeline...'}),
        }


class FarmSurveySubmissionForm(forms.ModelForm):
    """Individual survey questionnaire submission form."""
    class Meta:
        model = FarmSurveySubmission
        fields = ['campaign', 'farmer', 'sector', 'crop', 'area_planted_ha', 'quantity_harvested_kg', 'yield_kg_per_ha']
        widgets = {
            'campaign': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'farmer': forms.Select(attrs={'class': 'dash-select-input'}),
            'sector': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'crop': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'area_planted_ha': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.01', 'required': True}),
            'quantity_harvested_kg': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.01'}),
            'yield_kg_per_ha': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.01'}),
        }


class DistrictSocioeconomicProfileForm(forms.ModelForm):
    """NISR AHS District Socioeconomic Profile Form."""
    class Meta:
        model = DistrictSocioeconomicProfile
        fields = [
            'district', 'survey_year', 'provenance',
            'sample_households_count', 'total_plots_surveyed',
            'extension_advisory_reach_pct', 'twigire_muhinzi_membership_pct',
            'credit_access_pct', 'sacco_credit_share_pct', 'bank_credit_share_pct',
            'formal_land_title_pct', 'avg_plots_per_household', 'avg_plot_area_sqm',
            'sustainable_practices_pct', 'dairy_producing_households_pct',
        ]
        widgets = {
            'district': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'survey_year': forms.NumberInput(attrs={'class': 'dash-text-input', 'required': True}),
            'provenance': forms.TextInput(attrs={'class': 'dash-text-input'}),
            'sample_households_count': forms.NumberInput(attrs={'class': 'dash-text-input', 'min': 0}),
            'total_plots_surveyed': forms.NumberInput(attrs={'class': 'dash-text-input', 'min': 0}),
            'extension_advisory_reach_pct': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.1', 'min': 0, 'max': 100}),
            'twigire_muhinzi_membership_pct': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.1', 'min': 0, 'max': 100}),
            'credit_access_pct': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.1', 'min': 0, 'max': 100}),
            'sacco_credit_share_pct': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.1', 'min': 0, 'max': 100}),
            'bank_credit_share_pct': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.1', 'min': 0, 'max': 100}),
            'formal_land_title_pct': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.1', 'min': 0, 'max': 100}),
            'avg_plots_per_household': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.01', 'min': 0}),
            'avg_plot_area_sqm': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.1', 'min': 0}),
            'sustainable_practices_pct': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.1', 'min': 0, 'max': 100}),
            'dairy_producing_households_pct': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.1', 'min': 0, 'max': 100}),
        }

