import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_data_updated_success(client, make_user, profile_form_data):
    created_user = make_user()

    client.force_login(user=created_user)

    expected_avatar_name = profile_form_data["avatar"].name.split('.')[0]

    url = reverse("users:profile")
    response = client.post(url, data=profile_form_data)

    assert response.status_code == 302

    assert response.url == reverse("users:profile")

    created_user.refresh_from_db()

    assert created_user.first_name == profile_form_data["first_name"]

    assert created_user.last_name == profile_form_data["last_name"]

    assert created_user.username == profile_form_data["username"]

    assert created_user.email == profile_form_data["email"]

    assert created_user.phone == profile_form_data["phone"]

    assert created_user.avatar

    assert expected_avatar_name in created_user.avatar.name


@pytest.mark.parametrize("scenario_name, overrides", [
    ("long firstname", {"first_name": "a" * 151}),
    ("long lastname", {"last_name": "b" * 151}),
    ("empty username", {"username": ""}),
    ("username with spaces", {"username": "ivanov ivan ivanovich"}),
    ("username invalid chars", {"username": "ivan!@#$%."}),
    ("email_no_at", {"email": "invalidemail.com"}),
    ("email_no_user", {"email": "@example.com"}),
    ("email_no_domain", {"email": "invalid@"}),
    ("email_invalid_chars", {"email": "test user@ex.com"}),
    ("email_too_long", {"email": "a" * 250 + "@test.com"}),
    ("empty phone number", {"phone": ""}),
    ("long phone number", {"phone": "89123567365435"}),
])
@pytest.mark.django_db
def test_data_updated_fail(client, scenario_name, make_user, profile_form_data, overrides):
    created_user = make_user()
    client.force_login(user=created_user)

    old_data = {
        "first_name": created_user.first_name,
        "last_name": created_user.last_name,
        "username": created_user.username,
        "email": created_user.email,
        "phone": created_user.phone,
    }

    profile_form_data.update(overrides)

    url = reverse("users:profile")
    response = client.post(url, data=profile_form_data)

    assert response.status_code == 200

    created_user.refresh_from_db()

    for field_name in overrides.keys():
        assert field_name in response.context["form"].errors

    assert created_user.first_name == old_data["first_name"]
    assert created_user.last_name == old_data["last_name"]
    assert created_user.username == old_data["username"]
    assert created_user.email == old_data["email"]
    assert created_user.phone == old_data["phone"]


