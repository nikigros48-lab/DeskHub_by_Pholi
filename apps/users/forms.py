from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm



class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Псевдоним"
        self.fields["password"].label = "Пароль"


class CustomRegistrationForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("avatar", "first_name", "last_name", "username", "email", "phone")
        labels = {
            "avatar": "Фото профиля",
            "first_name": "Имя",
            "last_name": "Фамилия",
            "username": "Псевдоним",
            "email": "Электронная почта",
            "phone": "Номер телефона",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"


class ProfileForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("avatar", "first_name", "last_name", "username", "email", "phone")
        labels = {
            "avatar": "Фото профиля",
            "first_name": "Имя",
            "last_name": "Фамилия",
            "username": "Псевдоним",
            "email": "Электронная почта",
            "phone": "Номер телефона",
        }