"""
AgriLens Manual Agricultural Data Entry Forms.
Enforces server-side geographic validation, numeric bounds, and review workflow states.
"""
from django import forms
from django.core.exceptions import ValidationError
from apps.geography.models import Province, District, Sector
from apps.agriculture.models import AgriculturalSeason, Crop
from apps.data_management.models import ManualObservation, DataSource


class DataSourceForm(forms.ModelForm):
    """Form to register dynamic agricultural data sources with custom kinds, years, and seasons."""
    class Meta:
        model = DataSource
        fields = [
            'name', 'source_type', 'data_kind', 'year', 'season', 
            'organization', 'description', 'citation', 'is_official_survey'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. RAB Musanze Irish Potato Pilot 2026'}),
            'source_type': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. RAB_POTATO_2026_A (leave blank to auto-generate)'}),
            'data_kind': forms.Select(attrs={'class': 'form-select'}),
            'year': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 2026'}),
            'season': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. A, B, C, Annual, or All'}),
            'organization': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Rwanda Agriculture Board (RAB)'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Purpose, methodology, or coverage notes'}),
            'citation': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. RAB Research Report 2026/04'}),
            'is_official_survey': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['source_type'].required = False
        self.fields['description'].required = False
        self.fields['citation'].required = False
        self.fields['organization'].required = False
        self.fields['year'].required = False
        self.fields['season'].required = False


class ManualObservationForm(forms.ModelForm):
    province = forms.ModelChoiceField(
        queryset=Province.objects.all(),
        required=True,
        empty_label="Select Province",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_province'})
    )

    class Meta:
        model = ManualObservation
        fields = [
            'data_kind', 'data_source', 'season', 'province', 'district', 'sector', 'crop',
            'observation_date', 'reporting_organization', 'observation_reference',
            'plot_area_ha', 'total_production_kg',
            'is_irrigated', 'is_improved_seed', 'uses_inorganic_fertilizer',
            'uses_organic_fertilizer', 'has_soil_conservation', 'uses_mechanization',
            'inorganic_fertilizer_kg',
            'loss_quantity_kg', 'primary_loss_cause', 'quantity_sold_kg', 'farmgate_price_rwf',
            'latitude', 'longitude', 'gps_accuracy_m',
            'remarks'
        ]
        widgets = {
            'data_kind': forms.Select(attrs={'class': 'form-select', 'id': 'id_data_kind'}),
            'data_source': forms.Select(attrs={'class': 'form-select', 'id': 'id_data_source'}),
            'season': forms.Select(attrs={'class': 'form-select', 'id': 'id_season'}),
            'district': forms.Select(attrs={'class': 'form-select', 'id': 'id_district'}),
            'sector': forms.Select(attrs={'class': 'form-select', 'id': 'id_sector'}),
            'crop': forms.Select(attrs={'class': 'form-select'}),
            'observation_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'reporting_organization': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. MINAGRI / RAB / Sector Agronomist / Cooperative'}),
            'observation_reference': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. OBS-2026-MUS-042'}),
            'plot_area_ha': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.0001', 'placeholder': '0.0000'}),
            'total_production_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
            'inorganic_fertilizer_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00 kg'}),
            'loss_quantity_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
            'primary_loss_cause': forms.Select(attrs={'class': 'form-select'}),
            'quantity_sold_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
            'farmgate_price_rwf': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001', 'placeholder': 'e.g. -1.498300'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.000001', 'placeholder': 'e.g. 29.634100'}),
            'gps_accuracy_m': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.1', 'placeholder': 'e.g. 4.5'}),
            'remarks': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Contextual observations, field notes, or anomalies'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Order seasons and dynamic data sources cleanly
        if 'season' in self.fields:
            self.fields['season'].queryset = AgriculturalSeason.objects.all().order_by('-year', 'season')
        if 'data_source' in self.fields:
            self.fields['data_source'].queryset = DataSource.objects.all().order_by('-year', 'name')
            self.fields['data_source'].required = False
            self.fields['data_source'].empty_label = "-- Dynamic Auto-Generation (Based on Data Kind & Season) --"

        # Configure optional fields
        for opt_field in [
            'data_kind', 'data_source', 'inorganic_fertilizer_kg', 'loss_quantity_kg', 
            'primary_loss_cause', 'quantity_sold_kg', 'farmgate_price_rwf', 
            'latitude', 'longitude', 'gps_accuracy_m',
            'reporting_organization', 'observation_reference', 'remarks'
        ]:
            if opt_field in self.fields:
                self.fields[opt_field].required = False

        # Handle dependent dropdowns on POST or edit
        if 'province' in self.data:
            try:
                prov_id = int(self.data.get('province'))
                self.fields['district'].queryset = District.objects.filter(province_id=prov_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.district:
            self.fields['province'].initial = self.instance.district.province
            self.fields['district'].queryset = District.objects.filter(province=self.instance.district.province)
            self.fields['sector'].queryset = Sector.objects.filter(district=self.instance.district)
        else:
            self.fields['district'].queryset = District.objects.all()
            self.fields['sector'].queryset = Sector.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('data_kind'):
            cleaned_data['data_kind'] = DataSource.DataKind.EXTENSION_REPORT
        prov = cleaned_data.get('province')
        dist = cleaned_data.get('district')
        sec = cleaned_data.get('sector')

        # 1. Geographic Hierarchical Integrity Validation
        if prov and dist and dist.province != prov:
            self.add_error('district', f"District '{dist.name}' does not belong to {prov.name}.")

        if dist and sec and sec.district != dist:
            self.add_error('sector', f"Sector '{sec.name}' does not belong to {dist.name}.")

        # 2. Authoritative Server-side Validation Layer
        from apps.data_management.validation import validate_observation
        val_result = validate_observation(cleaned_data, instance_pk=self.instance.pk)
        self.validation_warnings = val_result.warnings
        self.validation_messages = val_result.messages

        for err in val_result.errors:
            field_name = err.get('field')
            msg = err['message']
            if field_name and field_name in self.fields:
                self.add_error(field_name, msg)
            else:
                self.add_error(None, msg)

        return cleaned_data
