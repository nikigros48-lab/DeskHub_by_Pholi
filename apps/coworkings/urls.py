from django.urls import path

from .views import CoworkingListView, CoworkingDetailView, PlaceListView, PlaceDetailView, CoworkingFilterView, \
    clear_filters

app_name = "coworking"

urlpatterns = [
    path("filters/", CoworkingFilterView.as_view(), name="filters"),
    path("clear/", clear_filters, name="clear_filters"),
    path('', CoworkingListView.as_view(), name="list"),
    path('<int:pk>/', CoworkingDetailView.as_view(), name="detail"),
    path("<int:coworking_id>/places/", PlaceListView.as_view(), name="place_list"),
    path("<int:coworking_id>/<int:pk>/", PlaceDetailView.as_view(), name="place_detail"),
]