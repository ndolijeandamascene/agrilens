from django import forms
from .models import Crop, CropCategory


class CropCategoryForm(forms.ModelForm):
    """Crop classification category form."""
    class Meta:
        model = CropCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Cereals, Legumes, Tubers', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'dash-textarea-input', 'rows': 3, 'placeholder': 'Category description and agronomic significance...'}),
        }


class CropForm(forms.ModelForm):
    """Crop taxonomy registration and update form."""
    class Meta:
        model = Crop
        fields = ['category', 'name', 'kinyarwanda_name', 'scientific_name', 'is_priority_crop', 'icon', 'image']
        widgets = {
            'category': forms.Select(attrs={'class': 'dash-select-input', 'required': True}),
            'name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Maize, Bush Beans, Irish Potato', 'required': True}),
            'kinyarwanda_name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Ibigori, Ibishyimbo, Ibirayi'}),
            'scientific_name': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. Zea mays, Phaseolus vulgaris'}),
            'is_priority_crop': forms.CheckboxInput(attrs={'style': 'width: 18px; height: 18px; cursor: pointer;'}),
            'icon': forms.TextInput(attrs={'class': 'dash-text-input', 'placeholder': 'e.g. cereal, legume, tuber, leaf'}),
        }
