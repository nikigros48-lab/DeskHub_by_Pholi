import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import ListView
from .models import Reservation
from ..coworkings.models import Slot

logger = logging.getLogger(__name__)


class CartReservationView(LoginRequiredMixin, View):
    def handle_no_permission(self):
        return redirect_to_login(
            reverse('cart:detail'),
            self.get_login_url(),
            self.get_redirect_field_name(),
        )

    def post(self, request, *args, **kwargs):
        cart = request.session.get('cart', [])
        if not cart:
            messages.warning(request, "Корзина пуста")
            return redirect("cart:detail")

        try:
            with transaction.atomic():
                created_reservations = []
                for item in cart:
                    slot_id = item.get('slot_id')
                    if not slot_id:
                        raise ValidationError("Некорректный элемент корзины: отсутствует slot_id")

                    try:
                        slot = Slot.objects.select_for_update().get(id=slot_id)
                    except Slot.DoesNotExist:
                        raise ValidationError(f"slot_missing:{slot_id}")

                    if getattr(slot, 'user', None) is not None:
                        raise ValidationError(f"slot_taken:{slot_id}:Слот {slot} уже занят другим пользователем.")

                    coworking = slot.place.coworking
                    coworking_tz = ZoneInfo(coworking.city.timezone)
                    now_coworking = datetime.now(coworking_tz).replace(tzinfo=None)

                    if slot.time_start <= now_coworking:
                        raise ValidationError(f"slot_expired:{slot_id}:Слот {slot} уже закончился.")

                    slot.user = request.user
                    slot.save(update_fields=['user'])

                    amount_people = item.get('amount_people', 1)

                    reservation = Reservation.objects.create(
                        user=request.user,
                        slot=slot,
                        status='awaiting',
                        amount_people=amount_people
                    )
                    created_reservations.append(reservation)

                request.session['cart'] = []
                messages.success(request, f"Забронировано {len(created_reservations)} слотов.")
                return redirect("reservation:requests")

        except ValidationError as e:
            error_text = e.messages[0] if e.messages else str(e)
            problem_slot_id = None

            for prefix in ("slot_missing:", "slot_taken:", "slot_expired:"):
                if error_text.startswith(prefix):
                    parts = error_text.split(":", 2)
                    try:
                        problem_slot_id = int(parts[1])
                    except (IndexError, ValueError):
                        problem_slot_id = None
                    error_text = parts[2] if len(parts) > 2 else "Этот слот больше недоступен."
                    break

            if problem_slot_id is not None:
                cart = request.session.get('cart', [])
                request.session['cart'] = [
                    i for i in cart if i.get('slot_id') != problem_slot_id
                ]

            messages.error(request, error_text)
            return redirect("cart:detail")
        except Exception:
            logger.exception("Ошибка при бронировании слотов из корзины")
            messages.error(request, "Произошла ошибка при бронировании. Попробуйте ещё раз.")
            return redirect("cart:detail")


class ReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "reservations/reservation_list.html"
    context_object_name = "reservations"
    ordering = "-created_at"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user=self.request.user).select_related(
            "slot", "slot__place", "slot__place__coworking", "slot__place__coworking__city"
        )


class CancelReservationView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        reservation_id = request.POST.get("reservation_id")

        if not reservation_id:
            messages.error(request, "Не указан ID бронирования.")
            return redirect("reservation:requests")

        reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)

        if reservation.status in ['cancelled', 'declined', 'completed']:
            messages.warning(request, "Это бронирование уже нельзя отменить.")
            return redirect("reservation:requests")

        reservation.status = "cancelled"
        reservation.save()
        messages.success(request, "Бронирование отменено.")
        return redirect("reservation:requests")