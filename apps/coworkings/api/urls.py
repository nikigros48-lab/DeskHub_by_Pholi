from django.urls import path
from .views import CoworkingListAPIView, PlaceSlotsAPIView

app_name = 'coworking_api'

urlpatterns = [
    path('coworkings/', CoworkingListAPIView.as_view(), name='coworking_list'),
    path('places/<int:place_id>/slots/', PlaceSlotsAPIView.as_view(), name='place_slots'),
]