import json
from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.cases.models import Asset, AssetMaintenanceEvent, AssetMaintenanceReminder, Property
from apps.taxonomy.models import Category

User = get_user_model()


@pytest.mark.django_db
def test_asset_maintenance_event_and_recurring_reminder_flow(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettrodomestici", slug="elettrodomestici-maintenance")
    property_obj = Property.objects.create(owner_user=user, name="Casa")
    asset = Asset.objects.create(property=property_obj, category=category, name="Lavatrice")
    client.force_login(user)

    event_response = client.post(
        reverse("api_v1:cases:asset-maintenance-event-list"),
        data=json.dumps(
            {
                "asset_id": asset.id,
                "event_type": AssetMaintenanceEvent.EventTypes.CLEANING,
                "title": "Pulizia filtro",
                "description": "Filtro pulito e verificato.",
                "event_date": "2026-05-09",
                "metadata_json": {"duration_minutes": 20},
            }
        ),
        content_type="application/json",
    )
    assert event_response.status_code == 201
    assert event_response.json()["asset_id"] == asset.id
    assert event_response.json()["property_id"] == property_obj.id
    assert event_response.json()["created_by_user_id"] == user.id

    event_list_response = client.get(
        reverse("api_v1:cases:asset-maintenance-event-list"),
        {"asset_id": asset.id},
    )
    assert event_list_response.status_code == 200
    assert [item["id"] for item in event_list_response.json()] == [event_response.json()["id"]]

    due_at = timezone.now() - timedelta(days=1)
    reminder_response = client.post(
        reverse("api_v1:cases:asset-maintenance-reminder-list"),
        data=json.dumps(
            {
                "asset_id": asset.id,
                "title": "Prossima pulizia filtro",
                "description": "Ricordare pulizia filtro lavatrice.",
                "due_at": due_at.isoformat(),
                "recurrence_rule": AssetMaintenanceReminder.RecurrenceRules.MONTHLY,
            }
        ),
        content_type="application/json",
    )
    assert reminder_response.status_code == 201
    reminder_id = reminder_response.json()["id"]
    assert reminder_response.json()["property_id"] == property_obj.id
    assert reminder_response.json()["status"] == AssetMaintenanceReminder.Statuses.ACTIVE

    complete_response = client.post(
        reverse("api_v1:cases:asset-maintenance-reminder-complete", args=[reminder_id]),
    )
    assert complete_response.status_code == 200
    completed_payload = complete_response.json()["reminder"]
    assert completed_payload["status"] == AssetMaintenanceReminder.Statuses.ACTIVE
    assert completed_payload["last_completed_at"] is not None
    assert completed_payload["due_at"] > reminder_response.json()["due_at"]

    reminder_list_response = client.get(
        reverse("api_v1:cases:asset-maintenance-reminder-list"),
        {"asset_id": asset.id, "status": AssetMaintenanceReminder.Statuses.ACTIVE},
    )
    assert reminder_list_response.status_code == 200
    assert [item["id"] for item in reminder_list_response.json()] == [reminder_id]


@pytest.mark.django_db
def test_asset_maintenance_permissions_and_context_validation(client):
    owner = User.objects.create_user(email="owner@example.com", password="Password123!")
    other_user = User.objects.create_user(email="other@example.com", password="Password123!")
    category = Category.objects.create(name="Clima", slug="clima-maintenance")
    property_obj = Property.objects.create(owner_user=owner, name="Casa")
    other_property = Property.objects.create(owner_user=owner, name="Garage")
    asset = Asset.objects.create(property=property_obj, category=category, name="Climatizzatore")
    event = AssetMaintenanceEvent.objects.create(
        asset=asset,
        property=property_obj,
        event_type=AssetMaintenanceEvent.EventTypes.INSPECTION,
        title="Controllo split",
        event_date="2026-05-09",
        created_by_user=owner,
    )

    client.force_login(other_user)
    assert client.get(reverse("api_v1:cases:asset-maintenance-event-detail", args=[event.id])).status_code == 404

    unauthorized_response = client.post(
        reverse("api_v1:cases:asset-maintenance-event-list"),
        data=json.dumps(
            {
                "asset_id": asset.id,
                "event_type": AssetMaintenanceEvent.EventTypes.NOTE,
                "title": "Nota non autorizzata",
                "event_date": "2026-05-09",
            }
        ),
        content_type="application/json",
    )
    assert unauthorized_response.status_code == 400
    assert unauthorized_response.json() == {"asset_id": ["You do not own this asset."]}

    client.force_login(owner)
    missing_context_response = client.post(
        reverse("api_v1:cases:asset-maintenance-reminder-list"),
        data=json.dumps(
            {
                "title": "Promemoria senza contesto",
                "due_at": timezone.now().isoformat(),
            }
        ),
        content_type="application/json",
    )
    assert missing_context_response.status_code == 400
    assert missing_context_response.json() == {
        "non_field_errors": ["At least one between asset_id and property_id is required."]
    }

    mismatch_response = client.post(
        reverse("api_v1:cases:asset-maintenance-reminder-list"),
        data=json.dumps(
            {
                "asset_id": asset.id,
                "property_id": other_property.id,
                "title": "Promemoria incoerente",
                "due_at": timezone.now().isoformat(),
            }
        ),
        content_type="application/json",
    )
    assert mismatch_response.status_code == 400
    assert mismatch_response.json() == {"asset_id": ["Asset does not belong to the selected property."]}


@pytest.mark.django_db
def test_non_recurring_reminder_is_completed(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Idraulica", slug="idraulica-maintenance")
    property_obj = Property.objects.create(owner_user=user, name="Casa")
    asset = Asset.objects.create(property=property_obj, category=category, name="Filtro acqua")
    reminder = AssetMaintenanceReminder.objects.create(
        asset=asset,
        property=property_obj,
        title="Sostituire filtro",
        due_at=timezone.now(),
        created_by_user=user,
    )
    client.force_login(user)

    response = client.post(reverse("api_v1:cases:asset-maintenance-reminder-complete", args=[reminder.id]))
    assert response.status_code == 200
    assert response.json()["reminder"]["status"] == AssetMaintenanceReminder.Statuses.COMPLETED
