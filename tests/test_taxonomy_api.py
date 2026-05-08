import pytest
from django.urls import reverse

from apps.taxonomy.models import Category, Tag


@pytest.mark.django_db
def test_categories_list_returns_only_active_categories(client):
    active_category = Category.objects.create(name="Elettricita", slug="elettricita", is_active=True)
    Category.objects.create(name="Idraulica", slug="idraulica", is_active=False)

    response = client.get(reverse("api_v1:taxonomy:category-list"))

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == active_category.id


@pytest.mark.django_db
def test_categories_list_supports_parent_id_and_is_root_filters(client):
    root = Category.objects.create(name="Impianti", slug="impianti")
    child = Category.objects.create(name="Elettricita", slug="elettricita", parent=root)
    Category.objects.create(name="Clima", slug="clima")

    root_response = client.get(reverse("api_v1:taxonomy:category-list"), {"is_root": "true"})
    assert root_response.status_code == 200
    assert {item["id"] for item in root_response.json()} == {root.id, Category.objects.get(slug="clima").id}

    child_response = client.get(reverse("api_v1:taxonomy:category-list"), {"parent_id": root.id})
    assert child_response.status_code == 200
    assert [item["id"] for item in child_response.json()] == [child.id]


@pytest.mark.django_db
def test_category_detail_returns_active_category(client):
    category = Category.objects.create(name="Domotica", slug="domotica")

    response = client.get(reverse("api_v1:taxonomy:category-detail", args=[category.id]))

    assert response.status_code == 200
    assert response.json()["slug"] == "domotica"


@pytest.mark.django_db
def test_tags_list_supports_category_and_search_filters(client):
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    matching_tag = Tag.objects.create(name="Salvavita", slug="salvavita", category=category)
    Tag.objects.create(name="Rubinetto", slug="rubinetto")
    Tag.objects.create(name="Inattivo", slug="inattivo", is_active=False)

    category_response = client.get(reverse("api_v1:taxonomy:tag-list"), {"category_id": category.id})
    assert category_response.status_code == 200
    assert [item["id"] for item in category_response.json()] == [matching_tag.id]

    search_response = client.get(reverse("api_v1:taxonomy:tag-list"), {"q": "salva"})
    assert search_response.status_code == 200
    assert [item["slug"] for item in search_response.json()] == ["salvavita"]


@pytest.mark.django_db
def test_tag_detail_returns_active_tag(client):
    tag = Tag.objects.create(name="Interruttore", slug="interruttore")

    response = client.get(reverse("api_v1:taxonomy:tag-detail", args=[tag.id]))

    assert response.status_code == 200
    assert response.json()["slug"] == "interruttore"
