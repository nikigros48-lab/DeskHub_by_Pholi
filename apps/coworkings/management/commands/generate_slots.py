from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
from django.core.management.base import BaseCommand
from apps.coworkings.models import Place, Slot


class Command(BaseCommand):
    help = "Генерирует слоты для всех мест на указанное количество дней вперёд"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Количество дней вперёд для генерации слотов (по умолчанию 30)"
        )

    def handle(self, *args, **options):
        days = options["days"]
        places = Place.objects.filter(is_active=True).select_related("coworking")
        total_created = 0

        for place in places:
            coworking = place.coworking
            work_start = coworking.work_time_start
            work_end = coworking.work_time_end

            if work_start >= work_end:
                self.stdout.write(self.style.WARNING(
                    f"Пропускаем коворкинг {coworking.name}: некорректное рабочее время"
                ))
                continue

            coworking_tz = ZoneInfo(coworking.city.timezone)
            today = datetime.now(coworking_tz).date()
            end_date = today + timedelta(days=days)

            self.stdout.write(
                f"[{coworking.name} / {place.name}] генерация слотов с {today} по {end_date}"
            )

            candidate_slots = []
            current_date = today
            while current_date <= end_date:
                slot_start = datetime.combine(current_date, work_start)
                slot_end = datetime.combine(current_date, work_end)

                current_slot_start = slot_start
                while current_slot_start < slot_end:
                    current_slot_end = current_slot_start + timedelta(hours=1)
                    if current_slot_end > slot_end:
                        break
                    candidate_slots.append((current_slot_start, current_slot_end))
                    current_slot_start = current_slot_end

                current_date += timedelta(days=1)

            if not candidate_slots:
                continue

            existing_starts = set(
                Slot.objects.filter(
                    place=place,
                    time_start__gte=candidate_slots[0][0],
                    time_start__lte=candidate_slots[-1][0],
                ).values_list("time_start", flat=True)
            )

            new_slots = [
                Slot(place=place, time_start=start, time_end=end, user=None)
                for start, end in candidate_slots
                if start not in existing_starts
            ]

            if not new_slots:
                continue

            created = Slot.objects.bulk_create(new_slots, batch_size=500)
            total_created += len(created)

        self.stdout.write(self.style.SUCCESS(
            f"Создано {total_created} слотов для {places.count()} мест"
        ))