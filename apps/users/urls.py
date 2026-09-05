from django.contrib.auth import views as auth_views
from django.urls import path

from apps.users.forms import CustomLoginForm
from apps.users.views import UserRegistrationView, UserUpdateView

app_name = 'users'

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="users/login.html", authentication_form=CustomLoginForm), name='login'),
    path("logout/", auth_views.LogoutView.as_view(), name='logout'),
    path("register/", UserRegistrationView.as_view(), name='registration'),
    path("profile/", UserUpdateView.as_view(), name='profile'),
]