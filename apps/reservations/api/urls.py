from django.urls import path

from apps.reservations.api.views import ReservationStatusAPIView

app_name = 'reservation_api'

urlpatterns = [
    path("reservations/<int:reservation_id>/status/", ReservationStatusAPIView.as_view(), name="status"),
]