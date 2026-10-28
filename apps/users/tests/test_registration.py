import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed

from apps.users.models import User

@pytest.mark.django_db
def test_registration_view_get(client):
    url = reverse("users:registration")
    response = client.get(url)

    assert response.status_code == 200
    assertTemplateUsed(response, "users/registration.html")

@pytest.mark.django_db
def test_registration_view_post_success(client, registration_form_data):
    url = reverse("users:registration")
    response = client.post(url, registration_form_data)

    assert response.status_code == 302
    assert response.url == reverse("info:main_page")

    assert User.objects.filter(username=registration_form_data["username"]).exists()

    assert "_auth_user_id" in client.session


@pytest.mark.parametrize("scenario_name, overrides", [
    ("Username is already taken", {"username": "testuser"}),
    ("Password is too short", {"password1": "0000", "password2": "0000"}),
    ("Phone is too long", {"phone": "89331639923123"}),
])
@pytest.mark.django_db
def test_registration_view_post_failure(client, registration_form_data, scenario_name, overrides, make_user):
    if scenario_name == "Username is already taken":
        make_user()

    users_count_before = User.objects.count()

    registration_form_data.update(overrides)

    url = reverse("users:registration")
    response = client.post(url, registration_form_data)

    assert response.status_code == 200

    assert User.objects.count() == users_count_before

    assert response.context["form"].errors
