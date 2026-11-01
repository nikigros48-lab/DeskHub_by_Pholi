import itertools
from dataclasses import dataclass
from datetime import time, date, timedelta, datetime, timezone
from freezegun import freeze_time
import pytest
from django.urls import reverse

from apps.coworkings.models import City, Coworking, Place, Slot


URL_NAMES = {
    "list": "coworking:list",
    "detail": "coworking:detail",
    "filter": "coworking:filters",
    "clear": "coworking:clear_filters",
    "places": "coworking:place_list",
    "place_detail": "coworking:place_detail",
    "api_list": "coworking_api:coworking_list",
    "api_slots": "coworking_api:place_slots",
}

FROZEN_UTC = datetime.combine(
    date.today() + timedelta(days=365), time(6, 0), tzinfo=timezone.utc
)

@pytest.fixture
def frozen_now():
    with freeze_time(FROZEN_UTC):
        yield FROZEN_UTC


@pytest.fixture
def url():
    def _url(alias: str, **kwargs) -> str:
        return reverse(URL_NAMES[alias], kwargs=kwargs or None)
    return _url


@pytest.fixture
def future_day() -> date:
    return date.today() + timedelta(days=2)


@pytest.fixture
def make_city():
    counter = itertools.count(1)

    def _create_city(name=None, timezone="Asia/Novosibirsk"):
        name = name or f"Город {next(counter)}"
        city, _ = City.objects.get_or_create(name=name, defaults={"timezone": timezone})
        return city

    return _create_city


@pytest.fixture
def make_coworking(make_city):
    counter = itertools.count(1)

    def _create_coworking(
        city=None,
        name=None,
        address=None,
        work_time_start=time(9, 0),
        work_time_end=time(18, 0),
    ) -> Coworking:
        n = next(counter)
        city = city or make_city()

        coworking, _ = Coworking.objects.get_or_create(
            city=city,
            address=address or f"Улица Тестовая, д. {n}",
            defaults={
                "name": name or f"Коворкинг {n}",
                "work_time_start": work_time_start,
                "work_time_end": work_time_end
            },
        )
        return coworking

    return _create_coworking


@pytest.fixture
def make_place(make_coworking):
    counter = itertools.count(1)

    def _create_place(
        coworking=None,
        name=None,
        place_type=Place.PlaceType.WORKPLACE,
        capacity=1,
        is_active=True
    ) -> Place:
        coworking = coworking or make_coworking()

        place, _ = Place.objects.get_or_create(
            coworking=coworking,
            name=name or f"Место {next(counter)}",
            type=place_type,
            defaults={"capacity": capacity, "is_active": is_active}
        )
        return place

    return _create_place


@pytest.fixture
def make_slot(make_place):
    def _create_slot(
            place=None,
            day=None,
            start=time(10, 0),
            end=time(11, 0),
            time_start=None,
            time_end=None,
            user=None,
    ) -> Slot:
        place = place or make_place()
        day = day or future_day

        return Slot.objects.create(
            place=place,
            time_start=time_start or datetime.combine(day, start),
            time_end=time_end or datetime.combine(day, end),
            user=user
        )

    return _create_slot


@dataclass
class TwoCities:
    city_1: City
    city_2: City
    coworking_1: Coworking
    coworking_2: Coworking


@pytest.fixture
def two_cities(make_city, make_coworking) -> TwoCities:
    city_1 = make_city(name="Новосибирск", timezone="Asia/Novosibirsk")
    city_2 = make_city(name="Красноярск", timezone="Asia/Novosibirsk")
    return TwoCities(
        city_1=city_1,
        city_2=city_2,
        coworking_1=make_coworking(city=city_1, name="Звезда", address="Ленина 17"),
        coworking_2=make_coworking(city=city_2, name="Популярный", address="Пушкина 20")
    )

