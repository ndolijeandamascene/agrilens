from django import forms
from .models import Cooperative, Farmer


class CooperativeForm(forms.ModelForm):
    """Agricultural Cooperative registration and update form."""
    class Meta:
        model = Cooperative
        fields = ['name', 'registration_number', 'sector', 'contact_phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. COOPAMA Musanze', 'required': True}),
            'registration_number': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. RCA/0892/2021'}),
            'sector': forms.Select(attrs={'class': 'dash-select-input'}),
            'contact_phone': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. +250 788 123 456'}),
        }


class FarmerForm(forms.ModelForm):
    """Smallholder farmer registration and update form."""
    class Meta:
        model = Farmer
        fields = ['first_name', 'last_name', 'national_id', 'gender', 'cooperative', 'sector', 'land_size_ha']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Jean', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Mugabo', 'required': True}),
            'national_id': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': '16-digit Rwandan NID'}),
            'gender': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'cooperative': forms.Select(attrs={'class': 'dash-select-input'}),
            'sector': forms.Select(attrs={'class': 'dash-select-input'}),
            'land_size_ha': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.01', 'placeholder': 'e.g. 0.75'}),
        }
