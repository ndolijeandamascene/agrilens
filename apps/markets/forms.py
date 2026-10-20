from django import forms
from django.utils import timezone
from apps.markets.models import CommodityPrice, MarketLocation, MarketCommodity, PricePublicNotice


class CommodityPriceForm(forms.ModelForm):
    """Manual price surveillance record entry form."""
    class Meta:
        model = CommodityPrice
        fields = [
            'market',
            'crop',
            'price_type',
            'price_per_kg_rwf',
            'wholesale_price_rwf',
            'farmgate_price_rwf',
            'unit',
            'date_recorded',
            'time_recorded',
            'source_type',
            'source_document',
        ]
        widgets = {
            'market': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'crop': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'price_type': forms.Select(attrs={'class': 'dash-select-input'}),
            'price_per_kg_rwf': forms.NumberInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. 420.00', 'step': '0.50', 'required': True}),
            'wholesale_price_rwf': forms.NumberInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. 390.00', 'step': '0.50'}),
            'farmgate_price_rwf': forms.NumberInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. 350.00', 'step': '0.50'}),
            'unit': forms.TextInput(attrs={'class': 'dash-text-input', 'value': 'RWF/kg'}),
            'date_recorded': forms.DateInput(attrs={'class': 'dash-text-input', 'type': 'date'}),
            'time_recorded': forms.TimeInput(attrs={'class': 'dash-text-input', 'type': 'time'}),
            'source_type': forms.Select(attrs={'class': 'dash-select-input'}),
            'source_document': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'Field Survey Reference ID or Slip #'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('date_recorded'):
            self.initial['date_recorded'] = timezone.now().date()
        if not self.initial.get('time_recorded'):
            self.initial['time_recorded'] = timezone.now().strftime('%H:%M')


class CommodityPriceCorrectionForm(forms.ModelForm):
    """Correction form with mandatory justification and audit lineage."""
    correction_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'dash-textarea-input',
            'rows': 3,
            'placeholder': 'State the verification rationale, source slip confirmation, or collector note...',
            'required': True,
        }),
        help_text="Required for audit compliance. Lineage will be preserved in the immutable audit log."
    )

    class Meta:
        model = CommodityPrice
        fields = [
            'price_per_kg_rwf',
            'wholesale_price_rwf',
            'farmgate_price_rwf',
            'unit',
            'correction_reason',
        ]
        widgets = {
            'price_per_kg_rwf': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.50', 'required': True}),
            'wholesale_price_rwf': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.50'}),
            'farmgate_price_rwf': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.50'}),
            'unit': forms.TextInput(attrs={'class': 'dash-text-input'}),
        }


class PriceCSVImportForm(forms.Form):
    """Bulk import spreadsheet form."""
    csv_file = forms.FileField(
        label="Select CSV File",
        help_text="CSV must contain headers: date, market, crop, retail_price, wholesale_price (optional), farmgate_price (optional)."
    )
    market_hub = forms.ModelChoiceField(
        queryset=MarketLocation.objects.filter(is_active=True),
        required=False,
        empty_label="Use Market Column from CSV",
        widget=forms.Select(attrs={'class': 'dash-select-input'})
    )


class MarketLocationForm(forms.ModelForm):
    """Register or update market hub."""
    class Meta:
        model = MarketLocation
        fields = ['name', 'district', 'province', 'market_type', 'is_major_hub', 'latitude', 'longitude', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Mahoko Commercial Market'}),
            'district': forms.Select(attrs={'class': 'dash-select-input'}),
            'province': forms.Select(attrs={'class': 'dash-select-input'}),
            'market_type': forms.Select(attrs={'class': 'dash-select-input'}),
            'latitude': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '0.000001'}),
        }


class MarketCommodityForm(forms.ModelForm):
    """Catalog item bounds configuration."""
    class Meta:
        model = MarketCommodity
        fields = ['name', 'crop', 'category', 'standard_unit', 'min_expected_price', 'max_expected_price', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'dash-text-input'}),
            'crop': forms.Select(attrs={'class': 'dash-select-input'}),
            'category': forms.Select(attrs={'class': 'dash-select-input'}),
            'standard_unit': forms.TextInput(attrs={'class': 'dash-text-input'}),
            'min_expected_price': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '1.00'}),
            'max_expected_price': forms.NumberInput(attrs={'class': 'dash-text-input', 'step': '1.00'}),
        }


class PricePublicNoticeForm(forms.ModelForm):
    """Publish price alerts or market notices."""
    class Meta:
        model = PricePublicNotice
        fields = ['title', 'message', 'severity', 'effective_date', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Season A Maize Price Stabilization Notice'}),
            'message': forms.Textarea(attrs={'class': 'dash-textarea-input', 'rows': 3}),
            'severity': forms.Select(attrs={'class': 'dash-select-input'}),
            'effective_date': forms.DateInput(attrs={'class': 'dash-text-input', 'type': 'date'}),
        }
