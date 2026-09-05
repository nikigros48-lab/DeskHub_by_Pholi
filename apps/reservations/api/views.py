from django.http import JsonResponse
from django.views import View

from apps.reservations.models import Reservation


class ReservationStatusAPIView(View):
    def get(self, request, reservation_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Требуется аутентификация"}, status=401)

        try:
            reservation = Reservation.objects.select_related("slot", "slot__place", "slot__place__coworking").get(id=reservation_id, user=request.user)
        except Reservation.DoesNotExist:
            return JsonResponse({"error": "Бронирование не найдено"}, status=404)

        return JsonResponse({
            "id": reservation.id,
            "status": reservation.status,
            "status_display": reservation.get_status_display(),
            "amount_people": reservation.amount_people,
            "place": str(reservation.slot.place) if reservation.slot else None,
            "created_at": reservation.created_at.isoformat(),
        })