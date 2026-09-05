from django.contrib import admin
from django.contrib import messages as admin_messages

from apps.reservations.models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "slot", "amount_people", "status", "created_at",)
    list_filter = ("status", "slot__place__coworking", "slot__place__type",)
    search_fields = ("id", "user__first_name", "user__last_name", "user__username",
                      "slot__place__name",)
    ordering = ("-created_at",)
    actions = ["approve_selected", "decline_selected", "mark_completed"]

    def _bulk_set_status(self, request, queryset, new_status, verb):
        updated = 0
        errors = 0
        for reservation in queryset:
            reservation.status = new_status
            try:
                reservation.save()
                updated += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f"Заявка #{reservation.id}: не удалось {verb} — {e}",
                    level=admin_messages.ERROR,
                )
        if updated:
            self.message_user(request, f"{verb.capitalize()}: {updated} заявок.")

    @admin.action(description="Подтвердить выбранные заявки")
    def approve_selected(self, request, queryset):
        self._bulk_set_status(request, queryset.filter(status="awaiting"), "approved", "подтвердить")

    @admin.action(description="Отклонить выбранные заявки")
    def decline_selected(self, request, queryset):
        self._bulk_set_status(request, queryset.filter(status="awaiting"), "declined", "отклонить")

    @admin.action(description="Отметить как завершённые")
    def mark_completed(self, request, queryset):
        self._bulk_set_status(request, queryset.filter(status="approved"), "completed", "завершить")