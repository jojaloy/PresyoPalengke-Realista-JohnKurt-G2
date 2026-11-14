import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User

PHONE_RE = re.compile(r'^(\+63|0)\d{10}$')


class RegisterForm(UserCreationForm):
    # Admins are never self-registered; they are created with `createsuperuser`.
    SELF_ROLES = [(User.Role.SHOPPER, 'Shopper'), (User.Role.VENDOR, 'Vendor')]

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=SELF_ROLES, label='I am a')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'role')

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_role(self):
        role = self.cleaned_data['role']
        if role not in (User.Role.SHOPPER, User.Role.VENDOR):
            raise forms.ValidationError('Invalid role.')
        return role

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Invalid username or password. Please try again.',
        'inactive': 'This account is inactive.',
    }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'contact_number',
                  'preferred_markets', 'profile_photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already used by another account.')
        return email

    def clean_contact_number(self):
        number = self.cleaned_data['contact_number'].replace(' ', '').replace('-', '')
        if number and not PHONE_RE.match(number):
            raise forms.ValidationError('Enter a valid PH number, e.g. 09171234567 or +639171234567.')
        return number

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if photo and hasattr(photo, 'size') and photo.size > 2 * 1024 * 1024:
            raise forms.ValidationError('Photo must be 2 MB or smaller.')
        return photo
