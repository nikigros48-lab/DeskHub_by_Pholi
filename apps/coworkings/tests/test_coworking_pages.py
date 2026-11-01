import pytest
from pytest_django.asserts import assertTemplateUsed

pytestmark = pytest.mark.django_db


def test_coworking_detail_ok(client, url, two_cities):
    response = client.get(url("detail", pk=two_cities.coworking_1.pk))

    assert response.status_code == 200
    assert response.context["coworking"] == two_cities.coworking_1
    assertTemplateUsed(response, "coworkings/coworking_detail.html")


def test_coworking_detail_unknown_pk_is_404(client, url):
    assert client.get(url("detail", pk=999999)).status_code == 404


@pytest.mark.parametrize(
    "alias, template",
    [
        ("list", "coworkings/coworking_list.html"),
        ("filter", "coworkings/coworking_filters.html"),
    ],
)
def test_pages_render_with_expected_template(auth_client, url, alias, template):
    response = auth_client.get(url(alias))

    assert response.status_code == 200
    assertTemplateUsed(response, template)

def test_place_list_page_renders(client, url, two_cities):
    response = client.get(url("places", coworking_id=two_cities.coworking_1.id))

    assert response.status_code == 200
    assertTemplateUsed(response, "coworkings/place_list.html")