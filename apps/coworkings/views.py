from datetime import datetime
from zoneinfo import ZoneInfo
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView, DetailView
from .models import Coworking, Place, City, Slot
from django.views.generic import FormView
from django.shortcuts import redirect
from .forms import CoworkingFilterForm


class CustomQSMixin:
    select_related_fields = ()

    def get_queryset(self):
        qs = super().get_queryset()
        if self.select_related_fields:
            qs = qs.select_related(*self.select_related_fields)
        return qs


class CoworkingListView(CustomQSMixin, ListView):
    model = Coworking
    context_object_name = "coworkings"
    template_name = "coworkings/coworking_list.html"
    select_related_fields = ("city",)

    def get_queryset(self):
        qs = super().get_queryset()

        selected_city = self.request.session.get("selected_city")
        if selected_city:
            qs = qs.filter(city__name=selected_city)

        place_type = self.request.session.get("place_type")
        if place_type:
            qs = qs.filter(place__type=place_type, place__is_active=True).distinct()

        filter_date_str = self.request.session.get("filter_date")
        if filter_date_str:
            try:
                filter_date = datetime.strptime(filter_date_str, '%Y-%m-%d').date()
            except ValueError:
                filter_date = None
        else:
            filter_date = None

        if filter_date:
            coworking_ids = list(qs.values_list('id', flat=True))

            slot_qs = Slot.objects.filter(
                place__coworking_id__in=coworking_ids,
                place__is_active=True,
                user__isnull=True,
                time_start__date=filter_date,
            ).select_related('place__coworking__city')

            if place_type:
                slot_qs = slot_qs.filter(place__type=place_type)

            valid_coworking_ids = set()
            now_cache = {}
            for slot in slot_qs:
                coworking = slot.place.coworking
                if coworking.id in valid_coworking_ids:
                    continue
                now_coworking = now_cache.get(coworking.city.timezone)
                if now_coworking is None:
                    now_coworking = datetime.now(ZoneInfo(coworking.city.timezone)).replace(tzinfo=None)
                    now_cache[coworking.city.timezone] = now_coworking
                if slot.time_start > now_coworking:
                    valid_coworking_ids.add(coworking.id)

            qs = qs.filter(id__in=valid_coworking_ids)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cities"] = City.objects.all()
        context["selected_city"] = self.request.session.get("selected_city")

        place_type = self.request.session.get("place_type")
        context["selected_place_type"] = place_type
        place_type_display = dict(Place.PLACE_TYPE).get(place_type, '')
        context["selected_place_type_display"] = place_type_display

        context["selected_date"] = self.request.session.get("filter_date")
        has_filters = any([
            context["selected_city"],
            context["selected_place_type"],
            context["selected_date"]
        ])
        context["has_filters"] = has_filters
        return context


class CoworkingDetailView(CustomQSMixin, DetailView):
    model = Coworking
    context_object_name = "coworking"
    template_name = "coworkings/coworking_detail.html"
    select_related_fields = ("city",)


class PlaceListView(ListView):
    model = Place
    context_object_name = "places"
    template_name = "coworkings/place_list.html"
    ordering = ["type", "name"]

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)
        coworking_id = self.kwargs.get("coworking_id") or self.request.GET.get("coworking_id")
        if coworking_id:
            qs = qs.filter(coworking_id=coworking_id)
        return qs


class PlaceDetailView(CustomQSMixin, DetailView):
    model = Place
    context_object_name = "place"
    template_name = "coworkings/place_detail.html"
    select_related_fields = ("coworking__city",)

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True).prefetch_related("slots")

    def get_context_data(self, **kwargs):
        cd = super().get_context_data(**kwargs)
        place = self.object
        coworking = place.coworking
        coworking_tz = ZoneInfo(coworking.city.timezone)

        date_str = self.request.GET.get('date')
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                selected_date = datetime.now().date()
        else:
            selected_date = datetime.now().date()

        filter_date = selected_date

        now_coworking = datetime.now(coworking_tz).replace(tzinfo=None)

        free_slots = place.slots.filter(
            user__isnull=True,
            time_start__date=filter_date,
            time_start__gt=now_coworking
        ).order_by('time_start')

        cd["free_slots"] = free_slots
        cd["selected_date"] = selected_date
        cd["filter_date"] = filter_date
        return cd


class CoworkingFilterView(LoginRequiredMixin, FormView):
    template_name = 'coworkings/coworking_filters.html'
    form_class = CoworkingFilterForm

    def get_initial(self):
        initial = {}
        city_name = self.request.session.get('selected_city')
        if city_name:
            try:
                initial['city'] = City.objects.get(name=city_name).id
            except City.DoesNotExist:
                pass
        initial['place_type'] = self.request.session.get('place_type', '')
        initial['date'] = self.request.session.get('filter_date', '')
        return initial

    def form_valid(self, form):
        city = form.cleaned_data.get('city')
        self.request.session['selected_city'] = city.name if city else None

        place_type = form.cleaned_data.get('place_type')
        self.request.session['place_type'] = place_type if place_type else None

        date = form.cleaned_data.get('date')
        self.request.session['filter_date'] = date.isoformat() if date else None

        return redirect('coworking:list')


class ClearFiltersView(View):
    def post(self, request):
        request.session.pop('selected_city', None)
        request.session.pop('place_type', None)
        request.session.pop('filter_date', None)
        return redirect('coworking:list')