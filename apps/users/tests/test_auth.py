import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_login_success(client, make_user):
    created_user = make_user()

    url = reverse('users:login')

    response = client.post(url, data={
        "username": created_user.username,
        "password": created_user.raw_password,
    })

    assert response.status_code == 302

    assert response.wsgi_request.user.is_authenticated

    assert response.wsgi_request.user.username == created_user.username


@pytest.mark.parametrize("scenario_name, overrides", [
    ("wrong username",{"username": "__wrong Username__"}),
    ("wrong password",{"password": "__WrOnGPassWord__"}),
])
@pytest.mark.django_db
def test_login_failure(client, scenario_name, make_user, overrides):
    created_user = make_user()

    login_data = {
        "username": created_user.username,
        "password": created_user.raw_password,
    }
    login_data.update(overrides)

    url = reverse('users:login')
    response = client.post(url, data=login_data)

    assert response.status_code == 200

    assert response.context["form"].errors

    assert response.wsgi_request.user.is_anonymous


@pytest.mark.django_db
def test_logout(client, make_user):
    client.force_login(make_user())

    url = reverse("users:logout")
    response = client.post(url)

    assert response.status_code == 302

    assert response.wsgi_request.user.is_anonymous