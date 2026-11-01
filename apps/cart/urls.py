from django.urls import path

from .views import CartDetailView, clear_cart, delete_from_cart, add_slots_to_cart

app_name = 'cart'

urlpatterns = [
    path('', CartDetailView.as_view(), name='detail'),
    path('clear/', clear_cart, name='clear'),
    path('delete/', delete_from_cart, name='delete_item'),
    path("add/", add_slots_to_cart, name='add_item'),
]