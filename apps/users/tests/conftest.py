import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def make_user(django_user_model):
    def _create_user(**kwargs):
        defaults = {
            "username": 'testuser',
            "password": "Test_password123",
            "phone": "89991639999",
        }

        defaults.update(kwargs)

        user = django_user_model.objects.create_user(**defaults)

        user.raw_password = defaults["password"] # type: ignore

        return user
    return _create_user


@pytest.fixture
def profile_form_data():
    small_gif = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00!\xf9\x04'
        b'\x01\x0a\x00\x01\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
        b'\x02L\x01\x00;'
    )
    fake_avatar = SimpleUploadedFile(
        name='test_avatar.gif',
        content=small_gif,
        content_type='image/gif'
    )

    return {
        "avatar": fake_avatar,
        "first_name": "TestNamechanged",
        "last_name": "TestLastNamechanged",
        "username": "TestUsernamechanged",
        "email": "test_email@changed.com",
        "phone": "89001694354",
    }

@pytest.fixture
def registration_form_data(profile_form_data):
    data = profile_form_data.copy()
    data.pop("avatar", None)
    data["password1"] = "Test_password123"
    data["password2"] = "Test_password123"
    return data


@pytest.fixture(autouse=True)
def mock_media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "test_media"