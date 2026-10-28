import pytest
from django.urls import reverse
from pytest_django.asserts import assertTemplateUsed


@pytest.mark.parametrize("url_name, expected_template", [
    ("info:main_page", "info/main_page.html"),
    ("info:about", "info/about.html"),
    ("info:contacts", "info/contacts.html"),
])
def test_info_static_pages(client, url_name, expected_template):
    url = reverse(url_name)
    response = client.get(url)

    assert response.status_code == 200

    assertTemplateUsed(response, expected_template)