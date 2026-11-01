from datetime import time, timedelta

import pytest
from freezegun import freeze_time

from apps.coworkings.models import Place

pytestmark = pytest.mark.django_db

WORKPLACE = Place.PlaceType.WORKPLACE
MEETING_ROOM = Place.PlaceType.MEETING_ROOM

BAD_DATES = ["abc", "2030-13-45", "31.12.2030", "2030-01-15T10:00:00"]


@pytest.fixture
def api_list(client, url):
    def _get(**params):
        return client.get(url("api_list"), params)

    return _get


@pytest.fixture
def api_slots(client, url):
    def _get(target_place, **params):
        return client.get(url("api_slots", place_id=target_place.pk), params)

    return _get


@pytest.fixture
def place(two_cities, make_place):
    return make_place(coworking=two_cities.coworking_1)


def ids(response) -> set:
    return {item["id"] for item in response.json()["results"]}



def test_list_without_params_returns_all(api_list, two_cities):
    response = api_list()

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    assert response.json()["count"] == 2
    assert ids(response) == {two_cities.coworking_1.id, two_cities.coworking_2.id}


def test_list_item_format(api_list, two_cities):
    item = api_list(city=two_cities.city_1.name).json()["results"][0]
    cw = two_cities.coworking_1

    assert item == {
        "id": cw.id,
        "name": cw.name,
        "city": two_cities.city_1.name,
        "address": cw.address,
        "work_time_start": "09:00",
        "work_time_end": "18:00",
    }


@pytest.mark.parametrize(
    "city_attr, coworking_attr",
    [("city_1", "coworking_1"), ("city_2", "coworking_2")],
)
def test_list_filter_by_city(api_list, two_cities, city_attr, coworking_attr):
    response = api_list(city=getattr(two_cities, city_attr).name)

    assert ids(response) == {getattr(two_cities, coworking_attr).id}
    assert response.json()["count"] == 1


def test_list_unknown_city_returns_empty(api_list, two_cities):
    response = api_list(city="Атлантида")

    assert response.status_code == 200
    assert response.json() == {"results": [], "count": 0}


@pytest.mark.parametrize(
    "place_type, coworking_attr",
    [(WORKPLACE, "coworking_1"), (MEETING_ROOM, "coworking_2")],
)
def test_list_filter_by_place_type(api_list, two_cities, make_place, place_type, coworking_attr):
    make_place(coworking=two_cities.coworking_1, place_type=WORKPLACE)
    make_place(coworking=two_cities.coworking_2, place_type=MEETING_ROOM)

    response = api_list(place_type=place_type.value)

    assert ids(response) == {getattr(two_cities, coworking_attr).id}


def test_list_invalid_place_type_is_400(api_list, two_cities):
    response = api_list(place_type="Nonsense")

    assert response.status_code == 400
    assert "place_type" in response.json()["error"]


def test_list_place_type_ignores_inactive_places(api_list, two_cities, make_place):
    make_place(coworking=two_cities.coworking_1)
    make_place(coworking=two_cities.coworking_2, is_active=False)

    assert ids(api_list(place_type=WORKPLACE.value)) == {two_cities.coworking_1.id}


def test_list_place_type_does_not_duplicate_coworkings(api_list, two_cities, make_place):
    make_place(coworking=two_cities.coworking_1)
    make_place(coworking=two_cities.coworking_1)

    response = api_list(place_type=WORKPLACE.value)

    assert response.json()["count"] == 1
    assert len(response.json()["results"]) == 1


def test_list_filter_by_date_shows_coworking_with_free_slot(api_list, two_cities, make_place, make_slot, future_day):
    make_slot(place=make_place(coworking=two_cities.coworking_1), day=future_day)
    make_place(coworking=two_cities.coworking_2)

    response = api_list(date=future_day.isoformat())

    assert ids(response) == {two_cities.coworking_1.id}


def test_list_filter_by_date_ignores_booked_slots(api_list, two_cities, make_place, make_slot, make_user, future_day):
    make_slot(place=make_place(coworking=two_cities.coworking_1), day=future_day)
    make_slot(place=make_place(coworking=two_cities.coworking_2), day=future_day, user=make_user())

    assert ids(api_list(date=future_day.isoformat())) == {two_cities.coworking_1.id}


def test_list_filter_by_date_ignores_other_dates_and_inactive_places(
    api_list, two_cities, make_place, make_slot, future_day
):
    make_slot(place=make_place(coworking=two_cities.coworking_1), day=future_day + timedelta(days=1))
    make_slot(place=make_place(coworking=two_cities.coworking_2, is_active=False), day=future_day)

    assert ids(api_list(date=future_day.isoformat())) == set()


def test_list_filter_by_date_works_for_any_future_day(api_list, two_cities, make_place, make_slot, future_day):
    make_slot(place=make_place(coworking=two_cities.coworking_1), day=future_day + timedelta(days=10))

    response = api_list(date=(future_day + timedelta(days=10)).isoformat())

    assert ids(response) == {two_cities.coworking_1.id}


@pytest.mark.parametrize("bad_date", BAD_DATES)
def test_list_invalid_date_is_400(api_list, two_cities, bad_date):
    response = api_list(date=bad_date)

    assert response.status_code == 400
    assert "YYYY-MM-DD" in response.json()["error"]


@pytest.mark.parametrize(
    "start, expected_shown",
    [
        (time(12, 59), False),
        (time(13, 0), False),
        (time(13, 1), True),
        (time(15, 0), True),
    ],
)
def test_list_filter_by_date_hides_started_slots(
    api_list, two_cities, make_place, make_slot, frozen_now, start, expected_shown
):
    day = frozen_now.date()
    make_slot(
        place=make_place(coworking=two_cities.coworking_1),
        day=day, start=start, end=time(start.hour + 1, start.minute),
    )

    response = api_list(date=day.isoformat())

    assert ids(response) == ({two_cities.coworking_1.id} if expected_shown else set())


def test_list_filter_by_date_uses_timezone_of_each_city(
    api_list, make_city, make_coworking, make_place, make_slot, frozen_now
):
    cw_nsk = make_coworking(city=make_city(name="Новосибирск", timezone="Asia/Novosibirsk"))
    cw_msk = make_coworking(city=make_city(name="Москва", timezone="Europe/Moscow"))
    day = frozen_now.date()
    for coworking in (cw_nsk, cw_msk):
        make_slot(place=make_place(coworking=coworking), day=day, start=time(11), end=time(12))

    assert ids(api_list(date=day.isoformat())) == {cw_msk.id}


def test_list_filter_by_type_and_date_counts_only_slots_of_that_type(
    api_list, two_cities, make_place, make_slot, future_day
):
    make_place(coworking=two_cities.coworking_1, place_type=WORKPLACE)
    make_slot(place=make_place(coworking=two_cities.coworking_1, place_type=MEETING_ROOM), day=future_day)
    make_slot(place=make_place(coworking=two_cities.coworking_2, place_type=WORKPLACE), day=future_day)

    response = api_list(place_type=WORKPLACE.value, date=future_day.isoformat())

    assert ids(response) == {two_cities.coworking_2.id}


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_list_allows_only_get(client, url, method):
    assert getattr(client, method)(url("api_list")).status_code == 405


def test_slots_response_format(api_slots, two_cities, make_place, make_slot, future_day):
    target = make_place(coworking=two_cities.coworking_1, capacity=3)
    slot = make_slot(place=target, day=future_day, start=time(10), end=time(11))

    response = api_slots(target, date=future_day.isoformat())

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    assert response.json() == {
        "place_id": target.id,
        "place_name": str(target),
        "capacity": 3,
        "date": future_day.isoformat(),
        "free_slots": [{"id": slot.id, "time_start": "10:00", "time_end": "11:00"}],
    }


def test_slots_unknown_place_is_404(client, url):
    response = client.get(url("api_slots", place_id=999999))

    assert response.status_code == 404
    assert response.json() == {"error": "Место не найдено"}


def test_slots_inactive_place_is_404(client, url, two_cities, make_place):
    inactive = make_place(coworking=two_cities.coworking_1, is_active=False)

    assert client.get(url("api_slots", place_id=inactive.pk)).status_code == 404


def test_slots_contain_only_free_slots_of_this_place_and_date(
    api_slots, place, make_place, make_slot, make_user, future_day
):
    free = make_slot(place=place, day=future_day, start=time(10), end=time(11))
    make_slot(place=place, day=future_day, start=time(11), end=time(12), user=make_user())
    make_slot(place=place, day=future_day + timedelta(days=1))
    make_slot(place=make_place(coworking=place.coworking), day=future_day)

    response = api_slots(place, date=future_day.isoformat())

    assert [s["id"] for s in response.json()["free_slots"]] == [free.id]


def test_slots_are_ordered_by_start_time(api_slots, place, make_slot, future_day):
    s14 = make_slot(place=place, day=future_day, start=time(14), end=time(15))
    s10 = make_slot(place=place, day=future_day, start=time(10), end=time(11))
    s12 = make_slot(place=place, day=future_day, start=time(12), end=time(13))

    response = api_slots(place, date=future_day.isoformat())

    assert [s["id"] for s in response.json()["free_slots"]] == [s10.id, s12.id, s14.id]


def test_slots_work_for_any_future_day(api_slots, place, make_slot, future_day):
    day = future_day + timedelta(days=10)
    slot = make_slot(place=place, day=day)

    response = api_slots(place, date=day.isoformat())

    assert [s["id"] for s in response.json()["free_slots"]] == [slot.id]


@pytest.mark.parametrize("bad_date", BAD_DATES)
def test_slots_invalid_date_is_400(api_slots, place, bad_date):
    response = api_slots(place, date=bad_date)

    assert response.status_code == 400
    assert "YYYY-MM-DD" in response.json()["error"]


@pytest.mark.parametrize(
    "start, expected_free",
    [
        (time(12, 59), False),
        (time(13, 0), False),
        (time(13, 1), True),
        (time(15, 0), True),
    ],
)
def test_slots_hide_started_slots(api_slots, place, make_slot, frozen_now, start, expected_free):
    day = frozen_now.date()
    slot = make_slot(place=place, day=day, start=start, end=time(start.hour + 1, start.minute))

    response = api_slots(place, date=day.isoformat())

    expected = [slot.id] if expected_free else []
    assert [s["id"] for s in response.json()["free_slots"]] == expected


@pytest.mark.parametrize(
    "timezone, expected_free",
    [("Asia/Novosibirsk", False), ("Europe/Moscow", True)],
)
def test_slots_use_timezone_of_coworking_city(
    api_slots, make_city, make_coworking, make_place, make_slot, frozen_now, timezone, expected_free
):
    city = make_city(name=f"Город {timezone}", timezone=timezone)
    target = make_place(coworking=make_coworking(city=city))
    day = frozen_now.date()
    slot = make_slot(place=target, day=day, start=time(11), end=time(12))

    response = api_slots(target, date=day.isoformat())

    expected = [slot.id] if expected_free else []
    assert [s["id"] for s in response.json()["free_slots"]] == expected


def test_slots_default_date_is_today_in_coworking_timezone(
    api_slots, make_city, make_coworking, make_place, frozen_now
):
    moscow = make_city(name="Москва", timezone="Europe/Moscow")
    target = make_place(coworking=make_coworking(city=moscow))

    with freeze_time(frozen_now.replace(hour=22)):
        response = api_slots(target)

    assert response.json()["date"] == (frozen_now.date() + timedelta(days=1)).isoformat()


def test_slots_default_date_returns_todays_free_slots(api_slots, place, make_slot, frozen_now):
    slot = make_slot(place=place, day=frozen_now.date(), start=time(15), end=time(16))

    response = api_slots(place)

    assert response.json()["date"] == frozen_now.date().isoformat()
    assert [s["id"] for s in response.json()["free_slots"]] == [slot.id]


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_slots_allow_only_get(client, url, place, method):
    assert getattr(client, method)(url("api_slots", place_id=place.pk)).status_code == 405