from django.urls import path

from apps.info.views import main_page, about, contacts

app_name = 'info'

urlpatterns = [
    path('', main_page, name='main_page'),
    path("about/", about, name='about'),
    path("contact/", contacts, name='contacts'),
]