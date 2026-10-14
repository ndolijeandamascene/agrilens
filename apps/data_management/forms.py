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
            'loss_quantity_kg', 'quantity_sold_kg', 'farmgate_price_rwf',
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
            'loss_quantity_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
            'quantity_sold_kg': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
            'farmgate_price_rwf': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'placeholder': '0.00'}),
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
        for opt_field in ['data_kind', 'data_source', 'loss_quantity_kg', 'quantity_sold_kg', 'farmgate_price_rwf', 'reporting_organization', 'observation_reference', 'remarks']:
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
        area = cleaned_data.get('plot_area_ha')
        prod = cleaned_data.get('total_production_kg')
        loss = cleaned_data.get('loss_quantity_kg')
        sold = cleaned_data.get('quantity_sold_kg')

        # 1. Server-side Geographic Hierarchical Integrity Validation
        if prov and dist and dist.province != prov:
            raise ValidationError({'district': f"District '{dist.name}' does not belong to {prov.name}."})

        if dist and sec and sec.district != dist:
            raise ValidationError({'sector': f"Sector '{sec.name}' does not belong to {dist.name}."})

        # 2. Area & Production Range Validation
        if area is not None and area <= 0:
            raise ValidationError({'plot_area_ha': "Plot area must be strictly positive (> 0 ha)."})

        if prod is not None and prod < 0:
            raise ValidationError({'total_production_kg': "Production quantity cannot be negative."})

        if loss is None:
            cleaned_data['loss_quantity_kg'] = 0.0
        elif loss < 0:
            raise ValidationError({'loss_quantity_kg': "Post-harvest loss quantity cannot be negative."})

        if sold is None:
            cleaned_data['quantity_sold_kg'] = 0.0
        elif prod is not None and sold > (prod + 100):
            raise ValidationError({'quantity_sold_kg': f"Sold quantity ({sold} kg) cannot significantly exceed total harvest ({prod} kg)."})

        return cleaned_data
