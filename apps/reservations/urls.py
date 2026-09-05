from django.urls import path

from apps.reservations.views import ReservationListView, CancelReservationView, CartReservationView

app_name = "reservation"
urlpatterns = [
    path("reserv/", CartReservationView.as_view(), name="create"),
    path("my-requests/", ReservationListView.as_view(), name="requests"),
    path("my-requests/cancel/", CancelReservationView.as_view(), name="cancel"),
]