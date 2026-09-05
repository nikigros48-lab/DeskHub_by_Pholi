from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.reservations.models import Reservation


class Command(BaseCommand):
    help = (
        "Обрабатывает просроченные заявки: "
        "1) отменяет заявки 'awaiting', на которые менеджер не отреагировал "
        "в течение RESERVATION_RESPONSE_DEADLINE_HOURS; "
        "2) переводит 'approved' в 'completed', если время слота уже прошло."
    )

    def handle(self, *args, **options):
        cancelled = self._cancel_overdue_awaiting()
        completed = self._complete_finished_approved()
        self.stdout.write(self.style.SUCCESS(
            f"Отменено просроченных заявок: {cancelled}. Завершено заявок: {completed}."
        ))

    def _cancel_overdue_awaiting(self):
        deadline_hours = settings.RESERVATION_RESPONSE_DEADLINE_HOURS
        cutoff = timezone.now() - timedelta(hours=deadline_hours)

        qs = Reservation.objects.filter(status='awaiting', created_at__lte=cutoff)
        count = 0
        for reservation in qs:
            reservation.status = 'cancelled'
            reservation.save()
            count += 1
        return count

    def _complete_finished_approved(self):
        qs = Reservation.objects.filter(status='approved').select_related(
            'slot', 'slot__place', 'slot__place__coworking', 'slot__place__coworking__city'
        )
        count = 0
        for reservation in qs:
            slot = reservation.slot
            if slot:
                city_tz = ZoneInfo(slot.place.coworking.city.timezone)
                now_local = datetime.now(city_tz).replace(tzinfo=None)
                if slot.time_end <= now_local:
                    reservation.status = 'completed'
                    reservation.save()
                    count += 1
        return count