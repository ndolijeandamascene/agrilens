from django import forms
from .models import SurveyCampaign, FarmSurveySubmission


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
