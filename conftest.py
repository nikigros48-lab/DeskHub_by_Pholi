import itertools

import pytest


@pytest.fixture
def make_user(django_user_model):
    counter = itertools.count(1)

    def _create_user(**kwargs):
        n : int = next(counter)
        defaults = {
            "username": f'testuser{n}',
            "password": "Test_password123",
            "phone": f"8999163{n:04d}",
        }

        defaults.update(kwargs)

        user = django_user_model.objects.create_user(**defaults)

        user.raw_password = defaults["password"] # type: ignore

        return user
    return _create_user


@pytest.fixture
def auth_client(client, make_user):
    client.force_login(make_user())
    return client


@pytest.fixture
def set_session(client):
    def _set(**values):
        session = client.session
        session.update(values)
        session.save()

    return _set