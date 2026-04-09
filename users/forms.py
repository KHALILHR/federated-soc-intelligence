from django import forms
from django.contrib.auth.password_validation import validate_password

from .models import Organization, User


class OrganizationForm(forms.ModelForm):
    """Form for creating and editing organizations."""

    class Meta:
        model = Organization
        fields = ['name', 'domain', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control-soc', 'placeholder': 'e.g. SOC Paris'}),
            'domain': forms.TextInput(attrs={'class': 'form-control-soc', 'placeholder': 'e.g. soc-paris.fr'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class UserCreateForm(forms.ModelForm):
    """Form for creating a new user within the manager's organization."""

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control-soc', 'placeholder': 'Password'}),
        validators=[validate_password],
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control-soc', 'placeholder': 'Confirm password'}),
        label='Confirm Password',
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'clearance_level', 'mfa_enabled']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control-soc', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control-soc', 'placeholder': 'user@example.com'}),
            'role': forms.Select(attrs={'class': 'form-control-soc'}),
            'clearance_level': forms.NumberInput(attrs={'class': 'form-control-soc', 'min': 1, 'max': 5}),
            'mfa_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')
        return cleaned_data


class UserEditForm(forms.ModelForm):
    """Form for editing an existing user (no password change here)."""

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'clearance_level', 'mfa_enabled']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control-soc'}),
            'email': forms.EmailInput(attrs={'class': 'form-control-soc'}),
            'role': forms.Select(attrs={'class': 'form-control-soc'}),
            'clearance_level': forms.NumberInput(attrs={'class': 'form-control-soc', 'min': 1, 'max': 5}),
            'mfa_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
