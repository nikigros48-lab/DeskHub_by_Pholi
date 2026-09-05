from django.contrib import admin
from apps.coworkings.models import City, Coworking, Place, Slot
from apps.users.models import User

admin.site.register(User)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "timezone",)
    list_filter = ("name", "timezone",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Coworking)
class CoworkingAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address",)
    list_filter = ("name", "city", "address",)
    search_fields = ("name", "city__name", "address",)


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "coworking", "capacity", "is_active",)
    list_filter = ("type", "is_active", "coworking__city",)
    search_fields = ("name", "coworking__name",)
    ordering = ("coworking", "type", "name",)

@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("place", "time_start", "time_end",)
    list_filter = ("place", "time_start", "time_end",)
    search_fields = ("place__type", "time_start", "time_end",)
    ordering = ("time_start", "time_end",)