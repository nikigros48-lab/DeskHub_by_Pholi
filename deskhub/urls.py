from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from deskhub import settings

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', include("apps.info.urls")),
    path('auth/', include("apps.users.urls")),
    path("coworkings/", include("apps.coworkings.urls")),
    path("reservations/", include("apps.reservations.urls")),
    path("cart/", include("apps.cart.urls")),
    # API
    path("api/", include("apps.coworkings.api.urls")),
    path("api/", include("apps.reservations.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
