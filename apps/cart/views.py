from django.contrib import messages
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView
from apps.coworkings.models import Slot


class CartDetailView(TemplateView):
    template_name = 'cart/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cart"] = self.request.session.get('cart', [])
        return context


class AddSlotsToCartView(View):
    def post(self, request, *args, **kwargs):
        slot_ids = request.POST.getlist('slot_ids')
        if not slot_ids:
            messages.error(request, "Вы не выбрали ни одного слота.")
            return redirect(request.META.get('HTTP_REFERER', 'coworking:list'))

        amount_people = request.POST.get('amount_people')
        try:
            amount_people = int(amount_people)
        except (TypeError, ValueError):
            amount_people = 1

        if amount_people < 1:
            amount_people = 1

        slots = Slot.objects.filter(id__in=slot_ids, user__isnull=True).select_related('place')
        if len(slots) != len(slot_ids):
            messages.error(request, "Некоторые из выбранных слотов уже заняты.")
            return redirect(request.META.get('HTTP_REFERER', 'coworking:list'))

        places_by_id = {}
        for slot in slots:
            places_by_id[slot.place_id] = slot.place

        for place in places_by_id.values():
            if amount_people > place.capacity:
                messages.error(
                    request,
                    f"Количество человек ({amount_people}) превышает вместимость места «{place}» ({place.capacity})."
                )
                return redirect(request.META.get('HTTP_REFERER', 'coworking:list'))

        cart = request.session.get('cart', [])
        existing_ids = [item.get('slot_id') for item in cart]
        added_count = 0
        for slot in slots:
            if slot.id not in existing_ids:
                cart.append({
                    'slot_id': slot.id,
                    'place_id': slot.place.id,
                    'place_name': str(slot.place),
                    'date': slot.time_start.date().isoformat(),
                    'time_start': slot.time_start.time().isoformat(),
                    'time_end': slot.time_end.time().isoformat(),
                    'amount_people': amount_people,
                })
                added_count += 1
                existing_ids.append(slot.id)

        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, f"Добавлено {added_count} слотов в корзину.")
        return redirect('cart:detail')


class DeleteFromCartView(View):
    def post(self, request, *args, **kwargs):
        slot_id = request.POST.get("slot_id")

        if slot_id is None:
            messages.error(request, "Такого элемента не существует")
            return redirect("cart:detail")

        try:
            slot_id = int(slot_id)
        except ValueError:
            messages.error(request, "Некорректный идентификатор слота")
            return redirect("cart:detail")

        cart = request.session.get('cart', [])
        new_cart = [item for item in cart if item.get('slot_id') != slot_id]

        if len(new_cart) == len(cart):
            messages.error(request, "Элемент не найден")
        else:
            removed = next((item for item in cart if item.get('slot_id') == slot_id), None)
            request.session['cart'] = new_cart
            request.session.modified = True
            if removed:
                messages.success(
                    request,
                    f"Удалён слот {removed.get('place_name')} на {removed.get('date')} "
                    f"с {removed.get('time_start')} по {removed.get('time_end')}"
                )
        return redirect("cart:detail")


class ClearCartView(View):
    def post(self, request, *args, **kwargs):
        request.session["cart"] = []
        request.session.modified = True
        messages.success(request, "Корзина очищена")
        return redirect("cart:detail")