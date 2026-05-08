import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from apps.cases.models import Asset, Case, Property
from apps.taxonomy.models import Category

User = get_user_model()


@pytest.mark.django_db
def test_attachment_upload_retrieve_and_delete_flow(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    property_obj = Property.objects.create(owner_user=user, name="Casa")
    asset = Asset.objects.create(property=property_obj, category=category, name="Quadro")
    case = Case.objects.create(customer_user=user, category=category, asset=asset, property=property_obj, title="Guasto")
    client.force_login(user)

    uploaded_file = SimpleUploadedFile("guasto.txt", b"contenuto test", content_type="text/plain")

    with override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        }
    ):
        create_response = client.post(
            reverse("api_v1:attachments:attachment-list"),
            data={
                "file": uploaded_file,
                "case_id": case.id,
                "asset_id": asset.id,
                "attachment_type": "document",
            },
        )
        assert create_response.status_code == 201
        attachment_id = create_response.json()["id"]

        detail_response = client.get(reverse("api_v1:attachments:attachment-detail", args=[attachment_id]))
        assert detail_response.status_code == 200
        assert detail_response.json()["file_name"] == "guasto.txt"

        delete_response = client.delete(reverse("api_v1:attachments:attachment-detail", args=[attachment_id]))
        assert delete_response.status_code == 204


@pytest.mark.django_db
def test_professional_can_upload_attachment_for_assigned_case_asset(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    property_obj = Property.objects.create(owner_user=customer, name="Casa")
    asset = Asset.objects.create(property=property_obj, category=category, name="Quadro")
    case = Case.objects.create(
        customer_user=customer,
        assigned_professional=professional,
        category=category,
        asset=asset,
        property=property_obj,
        title="Guasto",
    )
    client.force_login(professional)

    uploaded_file = SimpleUploadedFile("verbale.txt", b"contenuto test", content_type="text/plain")

    with override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        }
    ):
        create_response = client.post(
            reverse("api_v1:attachments:attachment-list"),
            data={
                "file": uploaded_file,
                "case_id": case.id,
                "asset_id": asset.id,
                "attachment_type": "document",
            },
        )
        assert create_response.status_code == 201


@pytest.mark.django_db
def test_attachment_rejects_asset_not_matching_case_property(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-attachments")
    property_obj = Property.objects.create(owner_user=customer, name="Casa")
    other_property = Property.objects.create(owner_user=customer, name="Garage")
    foreign_asset = Asset.objects.create(property=other_property, category=category, name="Pompa")
    case = Case.objects.create(customer_user=customer, category=category, property=property_obj, title="Guasto")
    client.force_login(customer)

    uploaded_file = SimpleUploadedFile("guasto.txt", b"contenuto test", content_type="text/plain")

    with override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        }
    ):
        create_response = client.post(
            reverse("api_v1:attachments:attachment-list"),
            data={
                "file": uploaded_file,
                "case_id": case.id,
                "asset_id": foreign_asset.id,
                "attachment_type": "document",
            },
        )
        assert create_response.status_code == 400
        assert create_response.json() == {"asset_id": ["Asset does not belong to the selected case property."]}


@pytest.mark.django_db
def test_attachment_rejects_upload_for_terminal_case(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Clima", slug="clima-terminal-attachments")
    case = Case.objects.create(
        customer_user=customer,
        category=category,
        title="Caso chiuso",
        status=Case.Statuses.CLOSED,
    )
    client.force_login(customer)

    uploaded_file = SimpleUploadedFile("chiuso.txt", b"contenuto test", content_type="text/plain")

    with override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
            "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
        }
    ):
        create_response = client.post(
            reverse("api_v1:attachments:attachment-list"),
            data={
                "file": uploaded_file,
                "case_id": case.id,
                "attachment_type": "document",
            },
        )
        assert create_response.status_code == 400
        assert create_response.json() == {
            "case_id": ["Attachments cannot be uploaded for a terminal case."]
        }
