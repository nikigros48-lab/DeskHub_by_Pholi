from django.urls import path

from .views import CartDetailView, ClearCartView, DeleteFromCartView, AddSlotsToCartView

app_name = 'cart'

urlpatterns = [
    path('', CartDetailView.as_view(), name='detail'),
    path('clear/', ClearCartView.as_view(), name='clear'),
    path('delete/', DeleteFromCartView.as_view(), name='delete_item'),
    path("add/", AddSlotsToCartView.as_view(), name='add_item'),
]