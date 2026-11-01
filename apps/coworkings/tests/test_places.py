from datetime import time, timedelta

import pytest
from freezegun import freeze_time

from apps.coworkings.models import Place


pytestmark = pytest.mark.django_db

WORKPLACE = Place.PlaceType.WORKPLACE
MEETING_ROOM = Place.PlaceType.MEETING_ROOM


def test_place_list_shows_only_active_places(client, url, two_cities, make_place):
    active = make_place(coworking=two_cities.coworking_1)
    make_place(coworking=two_cities.coworking_1, is_active=False)

    response = client.get(url("places", coworking_id=two_cities.coworking_1.id))

    assert response.status_code == 200
    assert set(response.context["places"]) == {active}


@pytest.mark.parametrize("coworking_attr", ["coworking_1", "coworking_2"])
def test_place_list_shows_only_places_of_this_coworking(client, url, two_cities, make_place, coworking_attr):
    places = {
        "coworking_1": make_place(coworking=two_cities.coworking_1),
        "coworking_2": make_place(coworking=two_cities.coworking_2),
    }
    coworking = getattr(two_cities, coworking_attr)

    response = client.get(url("places", coworking_id=coworking.id))

    assert set(response.context["places"]) == {places[coworking_attr]}


def test_place_list_unknown_coworking_id_returns_empty(client, url):
    response = client.get(url("places", coworking_id=999999))

    assert response.status_code == 200
    assert list(response.context["places"]) == []


def test_place_list_is_ordered_by_type_then_name(client, url, two_cities, make_place):
    b = make_place(coworking=two_cities.coworking_1, name="B", place_type=WORKPLACE)
    a = make_place(coworking=two_cities.coworking_1, name="A", place_type=WORKPLACE)
    z = make_place(coworking=two_cities.coworking_1, name="Z", place_type=MEETING_ROOM)

    response = client.get(url("places", coworking_id=two_cities.coworking_1.id))

    assert list(response.context["places"]) == [z, a, b]


@pytest.fixture
def place(two_cities, make_place):
    return make_place(coworking=two_cities.coworking_1)


@pytest.fixture
def get_detail(client, url):
    def _get(target_place, **query):
        return client.get(
            url("place_detail", coworking_id=target_place.coworking_id, pk=target_place.pk),
            query,
        )

    return _get


def test_place_detail_ok(get_detail, place):
    response = get_detail(place)

    assert response.status_code == 200
    assert response.context["place"] == place
    assert "free_slots" in response.context


def test_place_detail_inactive_place_is_404(client, url, two_cities, make_place):
    inactive = make_place(coworking=two_cities.coworking_1, is_active=False)

    response = client.get(url("place_detail", coworking_id=inactive.coworking_id, pk=inactive.pk))

    assert response.status_code == 404


def test_place_detail_unknown_pk_is_404(client, url, two_cities):
    response = client.get(url("place_detail", coworking_id=two_cities.coworking_1.id, pk=999999))

    assert response.status_code == 404


def test_free_slots_contain_only_free_slots_of_this_place_and_date(
    get_detail, place, make_place, make_slot, make_user, future_day
):
    free = make_slot(place=place, day=future_day, start=time(10), end=time(11))
    make_slot(place=place, day=future_day, start=time(11), end=time(12), user=make_user())  # занят
    make_slot(place=place, day=future_day + timedelta(days=1))  # другая дата
    make_slot(place=make_place(coworking=place.coworking), day=future_day)  # другое место

    response = get_detail(place, date=future_day.isoformat())

    assert list(response.context["free_slots"]) == [free]
    assert response.context["selected_date"] == future_day
    assert response.context["filter_date"] == future_day


def test_free_slots_are_ordered_by_start_time(get_detail, place, make_slot, future_day):
    s14 = make_slot(place=place, day=future_day, start=time(14), end=time(15))
    s10 = make_slot(place=place, day=future_day, start=time(10), end=time(11))
    s12 = make_slot(place=place, day=future_day, start=time(12), end=time(13))

    response = get_detail(place, date=future_day.isoformat())

    assert list(response.context["free_slots"]) == [s10, s12, s14]


@pytest.mark.parametrize(
    "start, expected_free",
    [
        (time(12, 59), False),
        (time(13, 0), False),
        (time(13, 1), True),
        (time(15, 0), True),
    ],
)
def test_free_slots_hide_slots_that_already_started(get_detail, place, make_slot, frozen_now, start, expected_free):
    day = frozen_now.date()
    slot = make_slot(place=place, day=day, start=start, end=time(start.hour + 1, start.minute))

    response = get_detail(place, date=day.isoformat())

    assert list(response.context["free_slots"]) == ([slot] if expected_free else [])


@pytest.mark.parametrize(
    "timezone, expected_free",
    [("Asia/Novosibirsk", False), ("Europe/Moscow", True)],
)
def test_free_slots_use_timezone_of_coworking_city(
    get_detail, make_city, make_coworking, make_place, make_slot, frozen_now, timezone, expected_free
):
    city = make_city(name=f"Город {timezone}", timezone=timezone)
    target = make_place(coworking=make_coworking(city=city))
    day = frozen_now.date()
    slot = make_slot(place=target, day=day, start=time(11), end=time(12))

    response = get_detail(target, date=day.isoformat())

    assert list(response.context["free_slots"]) == ([slot] if expected_free else [])


def test_default_date_is_today(get_detail, place, make_slot, frozen_now):
    day = frozen_now.date()
    slot = make_slot(place=place, day=day, start=time(15), end=time(16))

    response = get_detail(place)

    assert response.context["selected_date"] == day
    assert list(response.context["free_slots"]) == [slot]


@pytest.mark.parametrize("bad_date", ["abc", "2030-99-99", "15.01.2030"])
def test_invalid_date_falls_back_to_today(get_detail, place, frozen_now, bad_date):
    response = get_detail(place, date=bad_date)

    assert response.status_code == 200
    assert response.context["selected_date"] == frozen_now.date()



def test_default_date_is_today_in_coworking_timezone(get_detail, make_city, make_coworking, make_place, frozen_now):
    moscow = make_city(name="Москва", timezone="Europe/Moscow")
    target = make_place(coworking=make_coworking(city=moscow))

    with freeze_time(frozen_now.replace(hour=22)):
        response = get_detail(target)

    assert response.context["selected_date"] == frozen_now.date() + timedelta(days=1)