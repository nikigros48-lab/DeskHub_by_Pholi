from datetime import datetime
from zoneinfo import ZoneInfo
from django.http import JsonResponse
from django.views import View
from ...coworkings.models import Coworking, Place, Slot


class CoworkingListAPIView(View):
    def get(self,request, *args, **kwargs):
        qs = Coworking.objects.select_related("city").all()
        city = request.GET.get('city')
        if city:
            qs = qs.filter(city__name=city)

        place_type = request.GET.get('place_type')
        if place_type:
            if place_type not in dict(Place.PLACE_TYPE):
                return JsonResponse({'error': f'Недопустимый place_type. Варианты: {list(dict(Place.PLACE_TYPE).keys())}'}, status=400,)
            qs = qs.filter(place__type=place_type, place__is_active=True).distinct()

        date_str = request.GET.get("date")
        if date_str:
            try:
                filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({'error': 'date должен быть в формате YYYY-MM-DD'}, status=400)
            if filter_date:
                valid_ids = []
                for coworking in qs:
                    tz = ZoneInfo(coworking.city.timezone)
                    now_coworking = datetime.now(tz).replace(tzinfo=None)
                    slot_filters = {
                        "place__coworking": coworking,
                        "place__is_active": True,
                        "user__isnull": True,
                        "time_start__date": filter_date,
                        "time_end__date": now_coworking,
                    }
                    if place_type:
                        slot_filters["place__type"] = place_type
                    if Slot.objects.filter(**slot_filters).exists():
                        valid_ids.append(coworking.id)
                qs = qs.filter(id__in=valid_ids)

            data = [
                {
                    "id": c.id,
                    "name": c.name,
                    "city": c.city.name,
                    "address": c.address,
                    "work_time_start": c.work_time_start.strftime("%H:%M"),
                    "work_time_end": c.work_time_end.strftime("%H:%M"),
                }
                for c in qs
            ]
            return JsonResponse({"results": data, "count": len(data)},status=200)


class PlaceSlotsAPIView(View):
    def get(self,request, place_id, *args, **kwargs):
        try:
            place = Place.objects.select_related("coworking").get(id=place_id, is_active=True)
        except Place.DoesNotExist:
            return JsonResponse({"error": "Место не найдено"}, status=404)

        coworking_tz = ZoneInfo(place.coworking.city.timezone)

        date_str = request.GET.get("date")
        if date_str:
            try:
                target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                return JsonResponse({"error": "date должен быть в формате YYYY-MM-DD"}, status=400)
        else:
            target_date = datetime.now(coworking_tz).date()

        now_coworking = datetime.now(coworking_tz).replace(tzinfo=None)

        slots = place.slots.filter(
            user__isnull=True,
            time_start__date=target_date,
            time_end__date=now_coworking,
        ).order_by("time_start")

        data = [{"id": s.id, "time_start": s.time_start.strftime("%H:%M"), "time_end": s.time_end.strftime("%H:%M")} for s in slots]

        return JsonResponse({
            'place_id': place.id,
            'place_name': str(place),
            'capacity': place.capacity,
            'date': target_date.isoformat(),
            'free_slots': data,
        }, status=200)