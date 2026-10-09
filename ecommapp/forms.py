# forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Address  # Ensure Address model exists in models.py

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'address_line_1', 'address_line_2', 'city', 'state', 'postal_code', 'phone_number', 'is_default']