from datetime import date, timedelta

import pytest
from django.shortcuts import resolve_url

from apps.coworkings.models import Place
from deskhub import settings

pytestmark = pytest.mark.django_db

WORKPLACE = Place.PlaceType.WORKPLACE
MEETING_ROOM = Place.PlaceType.MEETING_ROOM

SOME_DATE = (date.today() + timedelta(days=30)).isoformat()

FIELD_TO_SESSION_KEY = {
    "city": "selected_city",
    "place_type": "place_type",
    "date": "filter_date",
}


@pytest.fixture
def valid_post_data(two_cities, future_day):
    return {
        "city": two_cities.city_1.id,
        "place_type": WORKPLACE.value,
        "date": future_day.isoformat(),
    }


@pytest.mark.parametrize("method", ["get", "post"])
def test_filter_view_requires_login(client, url, method):
    response = getattr(client, method)(url("filter"))

    assert response.status_code == 302
    assert response.url.startswith(resolve_url(settings.LOGIN_URL))


def test_get_renders_form(auth_client, url):
    response = auth_client.get(url("filter"))

    assert response.status_code == 200
    assert "form" in response.context


def test_get_prefills_form_from_session(auth_client, url, two_cities, set_session, future_day):
    set_session(
        selected_city=two_cities.city_1.name,
        place_type=WORKPLACE,
        filter_date=future_day.isoformat(),
    )

    initial = auth_client.get(url("filter")).context["form"].initial

    assert initial == {
        "city": two_cities.city_1.id,
        "place_type": WORKPLACE,
        "date": future_day.isoformat(),
    }


def test_get_with_empty_session_gives_empty_initial(auth_client, url):
    initial = auth_client.get(url("filter")).context["form"].initial

    assert initial == {"place_type": "", "date": ""}


def test_get_ignores_unknown_city_in_session(auth_client, url, set_session):
    set_session(selected_city="Атлантида")

    initial = auth_client.get(url("filter")).context["form"].initial

    assert "city" not in initial


def test_post_valid_saves_filters_to_session_and_redirects(
    auth_client, url, valid_post_data, two_cities, future_day
):
    response = auth_client.post(url("filter"), valid_post_data)

    assert response.status_code == 302
    assert response.url == url("list")
    session = auth_client.session
    assert session["selected_city"] == two_cities.city_1.name
    assert session["place_type"] == WORKPLACE
    assert session["filter_date"] == future_day.isoformat()


@pytest.mark.parametrize("field", list(FIELD_TO_SESSION_KEY))
def test_post_single_field_sets_only_its_session_key(auth_client, url, valid_post_data, field):
    auth_client.post(url("filter"), {field: valid_post_data[field]})

    session = auth_client.session
    for name, key in FIELD_TO_SESSION_KEY.items():
        if name == field:
            assert session[key] is not None
        else:
            assert session[key] is None


def test_post_empty_form_resets_filters(auth_client, url, set_session):
    set_session(selected_city="Новосибирск", place_type=WORKPLACE, filter_date=SOME_DATE)

    response = auth_client.post(url("filter"), {"city": "", "place_type": "", "date": ""})

    assert response.status_code == 302
    session = auth_client.session
    for key in FIELD_TO_SESSION_KEY.values():
        assert session[key] is None


@pytest.mark.parametrize(
    "bad_data",
    [{"place_type": "Nonsense"}, {"city": 999999}, {"date": "not-a-date"}],
    ids=["place_type", "city", "date"],
)
def test_post_invalid_data_rerenders_form_and_keeps_session(auth_client, url, set_session, bad_data):
    set_session(place_type=WORKPLACE)

    response = auth_client.post(url("filter"), bad_data)

    assert response.status_code == 200
    assert set(response.context["form"].errors) == set(bad_data)
    assert auth_client.session["place_type"] == WORKPLACE
    assert "selected_city" not in auth_client.session


@pytest.mark.parametrize("field", list(FIELD_TO_SESSION_KEY))
def test_applied_filter_changes_list(
    auth_client, url, two_cities, make_place, make_slot, future_day, valid_post_data, field
):
    make_slot(place=make_place(coworking=two_cities.coworking_1, place_type=WORKPLACE), day=future_day)
    make_place(coworking=two_cities.coworking_2, place_type=MEETING_ROOM)

    auth_client.post(url("filter"), {field: valid_post_data[field]})
    response = auth_client.get(url("list"))

    assert set(response.context["coworkings"]) == {two_cities.coworking_1}
    assert response.context["has_filters"] is True


def test_clear_filters_removes_filter_keys_and_redirects(client, url, set_session):
    set_session(selected_city="Новосибирск", place_type=WORKPLACE, filter_date=SOME_DATE, other="keep")

    response = client.post(url("clear"))

    assert response.status_code == 302
    assert response.url == url("list")
    session = client.session
    for key in FIELD_TO_SESSION_KEY.values():
        assert key not in session
    assert session["other"] == "keep"


def test_clear_filters_works_with_empty_session(client, url):
    assert client.post(url("clear")).status_code == 302


@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_clear_filters_allows_only_post(client, url, method):
    assert getattr(client, method)(url("clear")).status_code == 405


def test_clear_filters_restores_full_list(client, url, two_cities, set_session):
    set_session(selected_city=two_cities.city_1.name)
    client.post(url("clear"))

    response = client.get(url("list"))

    assert set(response.context["coworkings"]) == {two_cities.coworking_1, two_cities.coworking_2}
    assert response.context["has_filters"] is False