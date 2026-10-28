from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


class CustomRegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("avatar", "first_name", "last_name", "username", "email", "phone")


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("avatar", "first_name", "last_name", "username", "email", "phone")