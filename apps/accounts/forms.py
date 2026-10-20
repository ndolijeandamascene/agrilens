from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.core.exceptions import ValidationError
from apps.geography.models import Province, District
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={
            'class': 'auth-field-input',
            'id': 'id_username',
            'placeholder': 'Enter your username or email',
            'autocomplete': 'username',
            'required': True
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            'class': 'auth-field-input',
            'id': 'id_password',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'required': True
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'id': 'id_remember_me'})
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        if username and '@' in username:
            user = User.objects.filter(email__iexact=username.strip()).first()
            if user:
                self.cleaned_data['username'] = user.username
        return super().clean()


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'organization', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'organization': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
        }


class UserAdminCreationForm(forms.ModelForm):
    """
    Administrator form to register trusted internal officers and analysts.
    Initializes an unusable password so the officer must activate their account
    via a secure, single-use password setup link (Condition 6).
    """
    assigned_districts = forms.ModelMultipleChoiceField(
        queryset=District.objects.select_related('province').all().order_by('province__name', 'name'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select-multiple', 'style': 'min-height: 140px;'}),
        help_text="Hold Ctrl (or Cmd) to select multiple districts for geographic assignment."
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'role',
            'organization', 'phone_number', 'assigned_province', 'assigned_districts', 'is_active'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. j.nshimiyimana'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'official.email@minagri.gov.rw'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'organization': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. MINAGRI / NISR / RAB / District Agronomist'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+250 78... (optional)'}),
            'assigned_province': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['assigned_province'].queryset = Province.objects.all().order_by('name')
        self.fields['assigned_province'].empty_label = "-- National (No Specific Province) --"
        self.fields['is_active'].initial = True

    def save(self, commit=True):
        user = super().save(commit=False)
        # Sets unusable password; requires secure single-use link for activation
        user.set_unusable_password()
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserAdminEditForm(forms.ModelForm):
    """
    Administrator form to edit officer credentials, roles, and geographic assignments.
    Enforces strict lockout and privilege escalation protections.
    """
    assigned_districts = forms.ModelMultipleChoiceField(
        queryset=District.objects.select_related('province').all().order_by('province__name', 'name'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select-multiple', 'style': 'min-height: 140px;'}),
        help_text="Hold Ctrl (or Cmd) to select multiple districts for geographic assignment."
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'role',
            'organization', 'phone_number', 'assigned_province', 'assigned_districts', 'is_active'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'organization': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'assigned_province': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

    def __init__(self, *args, requesting_user=None, **kwargs):
        self.requesting_user = requesting_user
        super().__init__(*args, **kwargs)
        self.fields['assigned_province'].queryset = Province.objects.all().order_by('name')
        self.fields['assigned_province'].empty_label = "-- National (No Specific Province) --"

    def clean(self):
        cleaned_data = super().clean()
        instance = self.instance
        new_active = cleaned_data.get('is_active')
        new_role = cleaned_data.get('role')

        # Self-lockout prevention: Administrator cannot deactivate themselves
        if self.requesting_user and self.requesting_user.pk == instance.pk:
            if not new_active:
                raise ValidationError({'is_active': "Security Guard: You cannot deactivate your own administrative account."})
            if new_role != User.Role.ADMIN and self.requesting_user.role == User.Role.ADMIN:
                # Check if other active admins exist
                active_admins_count = User.objects.filter(role=User.Role.ADMIN, is_active=True).exclude(pk=instance.pk).count()
                if active_admins_count == 0:
                    raise ValidationError({'role': "Security Guard: You are the sole active Administrator. You cannot revoke your administrative privileges."})

        return cleaned_data


class PasswordSetupForm(SetPasswordForm):
    """Secure single-use token password setup form with standard validation."""
    pass


