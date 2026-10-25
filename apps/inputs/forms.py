from django import forms
from .models import InputCategory, AgriculturalInput


class InputCategoryForm(forms.ModelForm):
    """Input category form."""
    class Meta:
        model = InputCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Chemical Fertilizers, Improved Seeds', 'required': True}),
        }


class AgriculturalInputForm(forms.ModelForm):
    """Agricultural Input pricing and subsidy form."""
    class Meta:
        model = AgriculturalInput
        fields = ['category', 'name', 'unit', 'unit_price_rwf', 'subsidized_price_rwf']
        widgets = {
            'category': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. DAP Fertilizer, Hybrid Maize Seed H628', 'required': True}),
            'unit': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. kg, liter, bag', 'required': True}),
            'unit_price_rwf': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.01', 'placeholder': 'e.g. 1040.00', 'required': True}),
            'subsidized_price_rwf': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.01', 'placeholder': 'e.g. 640.00 (optional)'}),
        }
