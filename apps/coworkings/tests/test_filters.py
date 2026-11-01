from datetime import timedelta, date, time

import pytest

from apps.coworkings.models import Place, City

pytestmark = pytest.mark.django_db

WORKPLACE = Place.PlaceType.WORKPLACE
MEETING_ROOM = Place.PlaceType.MEETING_ROOM

SOME_DATE = (date.today() + timedelta(days=30)).isoformat()


@pytest.fixture
def get_list(client, url):
    def _get():
        response = client.get(url("list"))
        assert response.status_code == 200
        return response

    return _get

def shown(response) -> set:
    return set(response.context["coworkings"])


def test_no_filters_returns_all_coworkings(two_cities, get_list):
    response = get_list()

    assert shown(response) == {two_cities.coworking_1, two_cities.coworking_2}
    assert response.context["has_filters"] is False
    assert response.context["selected_place_type_display"] == ""
    assert set(response.context["cities"]) == {two_cities.city_1, two_cities.city_2}


def test_no_filters_keeps_coworking_without_active_places(two_cities, make_place, get_list):
    make_place(coworking=two_cities.coworking_1, is_active=False)

    assert shown(get_list()) == {two_cities.coworking_1, two_cities.coworking_2}


def test_none_values_in_session_behave_like_no_filters(two_cities, get_list, set_session):
    set_session(filter_date=None, selected_city=None, place_type=None)

    response = get_list()

    assert shown(response) == {two_cities.coworking_1, two_cities.coworking_2}
    assert response.context["has_filters"] is False


@pytest.mark.parametrize(
    "session_values",
    [
        pytest.param({"selected_city": "Новосибирск"}, id="city"),
        pytest.param({"place_type": WORKPLACE}, id="place_type"),
        pytest.param({"filter_date": SOME_DATE}, id="date"),
    ],
)
def test_has_filters_is_true_for_any_single_filter(set_session, get_list, session_values):
    set_session(**session_values)

    assert get_list().context["has_filters"] is True


@pytest.mark.parametrize(
    "city_attr, coworking_attr",
    [("city_1", "coworking_1"), ("city_2", "coworking_2")],
)
def test_filter_by_city(city_attr, coworking_attr, get_list, set_session, two_cities):
    city = getattr(two_cities, city_attr)
    set_session(selected_city=city.name)

    response = get_list()

    assert shown(response) == {getattr(two_cities, coworking_attr)}
    assert response.context["selected_city"] == city.name
    assert response.context["has_filters"] is True


def test_filter_by_unknown_city_returns_nothing(two_cities, get_list, set_session):
    set_session(selected_city="Открытый космос")

    assert shown(get_list()) == set()


@pytest.mark.parametrize(
    "place_type, coworking_attr",
    [(WORKPLACE, "coworking_1"), (MEETING_ROOM, "coworking_2")],
)
def test_filter_by_place_type(two_cities, make_place, set_session, get_list, place_type, coworking_attr):
    make_place(coworking=two_cities.coworking_1, place_type=WORKPLACE)
    make_place(coworking=two_cities.coworking_2, place_type=MEETING_ROOM)
    set_session(place_type=place_type)

    response = get_list()

    assert shown(response) == {getattr(two_cities, coworking_attr)}
    assert response.context["selected_place_type"] == place_type
    assert response.context["selected_place_type_display"] == place_type.label


@pytest.mark.parametrize("raw_value", ["Workplace", "Meeting_room"])
def test_place_type_raw_values_are_stable(two_cities, make_place, set_session, get_list, raw_value):
    make_place(coworking=two_cities.coworking_1, place_type=raw_value)
    set_session(place_type=raw_value)

    assert shown(get_list()) == {two_cities.coworking_1}


def test_filter_by_place_type_ignores_inactive_places(two_cities, make_place, get_list, set_session):
    make_place(coworking=two_cities.coworking_1, is_active=True)
    make_place(coworking=two_cities.coworking_2, is_active=False)
    set_session(place_type=WORKPLACE)

    assert shown(get_list()) == {two_cities.coworking_1}


def test_filter_by_place_type_does_not_duplicate_coworkings(two_cities, make_place, get_list, set_session):
    make_place(coworking=two_cities.coworking_1)
    make_place(coworking=two_cities.coworking_1)

    set_session(place_type=WORKPLACE)

    assert list(get_list().context["coworkings"]) == [two_cities.coworking_1]


@pytest.mark.parametrize("place_type", [WORKPLACE, MEETING_ROOM])
def test_coworking_with_several_types_matches_each_of_them(two_cities, make_place, set_session, get_list, place_type):
    make_place(coworking=two_cities.coworking_1, place_type=WORKPLACE)
    make_place(coworking=two_cities.coworking_1, place_type=MEETING_ROOM)
    set_session(place_type=place_type)

    assert shown(get_list()) == {two_cities.coworking_1}


def test_unknown_place_type_in_session_does_not_crash(two_cities, set_session, get_list):
    set_session(place_type="Nonsense")

    get_list()


def test_filter_by_date_shows_coworking_with_free_slot(two_cities, make_place, make_slot, set_session, future_day, get_list):
    make_slot(place=make_place(coworking=two_cities.coworking_1), day=future_day)
    make_place(coworking=two_cities.coworking_2)  # место есть, слотов нет
    set_session(filter_date=future_day.isoformat())

    response = get_list()

    assert shown(response) == {two_cities.coworking_1}
    assert response.context["selected_date"] == future_day.isoformat()
    assert response.context["has_filters"] is True


@pytest.mark.parametrize("booked_first", [True, False])
def test_filter_by_date_one_free_slot_is_enough_even_if_others_are_booked(
    two_cities, make_place, make_slot, make_user, set_session, future_day, get_list, booked_first
):
    user = make_user()
    place_1 = make_place(coworking=two_cities.coworking_1)
    place_2 = make_place(coworking=two_cities.coworking_2)

    booked = dict(place=place_1, day=future_day, start=time(10), end=time(11), user=user)
    free = dict(place=place_1, day=future_day, start=time(11), end=time(12))
    for kwargs in ([booked, free] if booked_first else [free, booked]):
        make_slot(**kwargs)
    make_slot(place=place_2, day=future_day, user=user)

    set_session(filter_date=future_day.isoformat())

    assert shown(get_list()) == {two_cities.coworking_1}


def test_filter_by_date_ignores_slots_on_other_dates(two_cities, make_place, make_slot, set_session, future_day, get_list):
    make_slot(place=make_place(coworking=two_cities.coworking_1), day=future_day + timedelta(days=1))
    set_session(filter_date=future_day.isoformat())

    assert shown(get_list()) == set()


def test_filter_by_date_ignores_slots_in_inactive_places(two_cities, make_place, make_slot, set_session, future_day, get_list):
    make_slot(place=make_place(coworking=two_cities.coworking_1, is_active=False), day=future_day)
    set_session(filter_date=future_day.isoformat())

    assert shown(get_list()) == set()


@pytest.mark.parametrize(
    "bad_value",
    ["not-a-date", "2030-13-45", "31.12.2030", "2030-01-15T10:00:00", 12345],
)
def test_invalid_filter_date_is_ignored(two_cities, set_session, get_list, bad_value):
    set_session(filter_date=bad_value)

    assert shown(get_list()) == {two_cities.coworking_1, two_cities.coworking_2}


@pytest.mark.parametrize(
    "start, expected_shown",
    [
        (time(12, 59), False),  # уже началось
        (time(13, 0), False),   # ровно «сейчас»: сравнение строгое
        (time(13, 1), True),
        (time(15, 0), True),
    ],
)
def test_filter_by_date_hides_slots_that_already_started(
    two_cities, make_place, make_slot, set_session, frozen_now, get_list, start, expected_shown
):
    day = frozen_now.date()
    make_slot(
        place=make_place(coworking=two_cities.coworking_1),
        day=day, start=start, end=time(start.hour + 1, start.minute),
    )
    set_session(filter_date=day.isoformat())

    assert shown(get_list()) == ({two_cities.coworking_1} if expected_shown else set())


def test_filter_by_date_uses_timezone_of_each_city(
    make_city, make_coworking, make_place, make_slot, set_session, frozen_now, get_list
):
    nsk = make_city(name="Новосибирск", timezone="Asia/Novosibirsk")
    msk = make_city(name="Москва", timezone="Europe/Moscow")
    cw_nsk = make_coworking(city=nsk)
    cw_msk = make_coworking(city=msk)
    day = frozen_now.date()
    for coworking in (cw_nsk, cw_msk):
        make_slot(place=make_place(coworking=coworking), day=day, start=time(11), end=time(12))
    set_session(filter_date=day.isoformat())

    assert shown(get_list()) == {cw_msk}


def test_filter_by_date_coworkings_with_same_timezone_all_shown(
    two_cities, make_place, make_slot, set_session, frozen_now, get_list
):
    day = frozen_now.date()
    for coworking in (two_cities.coworking_1, two_cities.coworking_2):
        make_slot(place=make_place(coworking=coworking), day=day, start=time(15), end=time(16))
    set_session(filter_date=day.isoformat())

    assert shown(get_list()) == {two_cities.coworking_1, two_cities.coworking_2}


def test_filter_by_type_and_date_counts_only_slots_of_that_type(
    two_cities, make_place, make_slot, set_session, future_day, get_list
):
    make_place(coworking=two_cities.coworking_1, place_type=WORKPLACE)
    make_slot(place=make_place(coworking=two_cities.coworking_1, place_type=MEETING_ROOM), day=future_day)
    make_slot(place=make_place(coworking=two_cities.coworking_2, place_type=WORKPLACE), day=future_day)
    set_session(place_type=WORKPLACE, filter_date=future_day.isoformat())

    assert shown(get_list()) == {two_cities.coworking_2}


def test_filter_by_city_and_place_type(two_cities, make_coworking, make_place, set_session, get_list):
    extra = make_coworking(city=two_cities.city_1)
    make_place(coworking=two_cities.coworking_1, place_type=WORKPLACE)
    make_place(coworking=extra, place_type=MEETING_ROOM)
    make_place(coworking=two_cities.coworking_2, place_type=WORKPLACE)
    set_session(selected_city=two_cities.city_1.name, place_type=WORKPLACE)

    assert shown(get_list()) == {two_cities.coworking_1}


def test_filter_by_city_type_and_date(
    two_cities, make_coworking, make_place, make_slot, set_session, future_day, get_list
):
    extra = make_coworking(city=two_cities.city_1)
    make_slot(place=make_place(coworking=two_cities.coworking_1, place_type=WORKPLACE), day=future_day)
    make_slot(place=make_place(coworking=extra, place_type=MEETING_ROOM), day=future_day)
    make_slot(place=make_place(coworking=two_cities.coworking_2, place_type=WORKPLACE), day=future_day)
    set_session(
        selected_city=two_cities.city_1.name,
        place_type=WORKPLACE,
        filter_date=future_day.isoformat(),
    )

    assert shown(get_list()) == {two_cities.coworking_1}


