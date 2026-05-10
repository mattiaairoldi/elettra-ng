import json

import pytest
from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.cases.models import Asset, Case, Property
from apps.taxonomy.models import Category
from apps.troubleshooting.models import DiagnosticFlow, DiagnosticNode, DiagnosticOption

User = get_user_model()


@pytest.mark.django_db
def test_property_and_asset_crud_for_customer(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    client.force_login(user)
    category = Category.objects.create(name="Elettricita", slug="elettricita")

    property_response = client.post(
        reverse("api_v1:cases:property-list"),
        data=json.dumps(
            {
                "name": "Casa Milano",
                "city": "Milano",
                "location": {"latitude": 45.4642, "longitude": 9.19},
            }
        ),
        content_type="application/json",
    )
    assert property_response.status_code == 201
    property_id = property_response.json()["id"]
    assert property_response.json()["location"] == {"latitude": 45.4642, "longitude": 9.19}
    assert Property.objects.get(id=property_id).location == Point(9.19, 45.4642, srid=4326)

    asset_response = client.post(
        reverse("api_v1:cases:asset-list"),
        data=json.dumps(
            {
                "property_id": property_id,
                "category_id": category.id,
                "name": "Quadro elettrico",
                "location_text": "Ingresso",
            }
        ),
        content_type="application/json",
    )
    assert asset_response.status_code == 201

    list_response = client.get(reverse("api_v1:cases:asset-list"), {"property_id": property_id})
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1


@pytest.mark.django_db
def test_case_creation_listing_and_detail_for_customer(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    client.force_login(user)
    category = Category.objects.create(name="Clima", slug="clima")
    property_obj = Property.objects.create(owner_user=user, name="Casa", city="Torino")
    asset = Asset.objects.create(property=property_obj, category=category, name="Climatizzatore")

    create_response = client.post(
        reverse("api_v1:cases:case-list"),
        data=json.dumps(
            {
                "category_id": category.id,
                "property_id": property_obj.id,
                "asset_id": asset.id,
                "title": "Climatizzatore non raffredda",
                "description": "Esce aria ma non fredda",
            }
        ),
        content_type="application/json",
    )
    assert create_response.status_code == 201
    case_id = create_response.json()["id"]

    list_response = client.get(reverse("api_v1:cases:case-list"))
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [case_id]

    detail_response = client.get(reverse("api_v1:cases:case-detail", args=[case_id]))
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "Climatizzatore non raffredda"


@pytest.mark.django_db
def test_case_creation_from_diagnosis_without_property_for_customer(client):
    user = User.objects.create_user(email="diagnosis@example.com", password="Password123!")
    client.force_login(user)
    category = Category.objects.create(name="Elettricita", slug="elettricita-diagnosis")

    response = client.post(
        reverse("api_v1:cases:case-list"),
        data=json.dumps(
            {
                "category_id": category.id,
                "title": "Diagnosi salvavita",
                "description": "Il salvavita scatta appena accendo il forno.",
                "priority": Case.Priorities.NORMAL,
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Diagnosi salvavita"
    assert payload["property_id"] is None
    assert payload["asset_id"] is None
    assert payload["owner_organization_id"]


@pytest.mark.django_db
def test_case_notes_and_events_endpoints(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    client.force_login(user)
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    case = Case.objects.create(customer_user=user, category=category, title="Salvavita abbassato")

    note_response = client.post(
        reverse("api_v1:cases:case-notes", args=[case.id]),
        data=json.dumps({"body": "Ho gia controllato il quadro."}),
        content_type="application/json",
    )
    assert note_response.status_code == 201

    notes_list_response = client.get(reverse("api_v1:cases:case-notes", args=[case.id]))
    assert notes_list_response.status_code == 200
    assert len(notes_list_response.json()) == 1

    events_response = client.get(reverse("api_v1:cases:case-events", args=[case.id]))
    assert events_response.status_code == 200
    assert len(events_response.json()) == 1


@pytest.mark.django_db
def test_case_status_assignment_and_troubleshooting_actions(client):
    admin = User.objects.create_user(email="admin@example.com", password="Password123!", role=User.Roles.ADMIN)
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    flow = DiagnosticFlow.objects.create(
        title="Salvavita abbassato",
        slug="salvavita-abbassato",
        category=category,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    node = DiagnosticNode.objects.create(
        flow=flow,
        title="Il salvavita scatta subito?",
        node_type=DiagnosticNode.NodeTypes.QUESTION,
        is_entrypoint=True,
    )
    next_node = DiagnosticNode.objects.create(
        flow=flow,
        title="Serve professionista",
        node_type=DiagnosticNode.NodeTypes.ESCALATION,
        sort_order=2,
    )
    option = DiagnosticOption.objects.create(from_node=node, to_node=next_node, label="Si")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")

    client.force_login(admin)
    assign_response = client.post(
        reverse("api_v1:cases:case-assign", args=[case.id]),
        data=json.dumps({"professional_user_id": professional.id}),
        content_type="application/json",
    )
    assert assign_response.status_code == 200
    case.refresh_from_db()
    assert case.assigned_professional_id == professional.id

    client.force_login(customer)
    start_response = client.post(
        reverse("api_v1:cases:case-troubleshooting-start", args=[case.id]),
        data=json.dumps({"flow_id": flow.id}),
        content_type="application/json",
    )
    assert start_response.status_code == 200
    case.refresh_from_db()
    assert case.troubleshooting_flow_id == flow.id
    assert case.current_diagnostic_node_id == node.id
    assert case.status == Case.Statuses.IN_DIAGNOSIS

    progress_response = client.post(
        reverse("api_v1:cases:case-troubleshooting-progress", args=[case.id]),
        data=json.dumps({"node_id": node.id, "option_id": option.id}),
        content_type="application/json",
    )
    assert progress_response.status_code == 200
    case.refresh_from_db()
    assert case.current_diagnostic_node_id == next_node.id

    client.force_login(professional)
    status_response = client.post(
        reverse("api_v1:cases:case-status", args=[case.id]),
        data=json.dumps({"status": Case.Statuses.RESOLVED}),
        content_type="application/json",
    )
    assert status_response.status_code == 200
    case.refresh_from_db()
    assert case.status == Case.Statuses.RESOLVED
    assert case.closed_at is not None


@pytest.mark.django_db
def test_case_status_permissions_and_transition_guards(client):
    admin = User.objects.create_user(email="admin@example.com", password="Password123!", role=User.Roles.ADMIN)
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    category = Category.objects.create(name="Clima", slug="clima-case-status-roles")
    case = Case.objects.create(
        customer_user=customer,
        assigned_professional=professional,
        category=category,
        title="Clima non raffredda",
        status=Case.Statuses.WAITING_PROFESSIONAL,
    )

    client.force_login(customer)
    invalid_customer_response = client.post(
        reverse("api_v1:cases:case-status", args=[case.id]),
        data=json.dumps({"status": Case.Statuses.IN_DIAGNOSIS}),
        content_type="application/json",
    )
    assert invalid_customer_response.status_code == 400
    assert invalid_customer_response.json() == {
        "status": ["Customers can only cancel a case or close a resolved one."]
    }

    cancel_response = client.post(
        reverse("api_v1:cases:case-status", args=[case.id]),
        data=json.dumps({"status": Case.Statuses.CANCELLED}),
        content_type="application/json",
    )
    assert cancel_response.status_code == 200

    case.status = Case.Statuses.RESOLVED
    case.save(update_fields=["status"])
    close_response = client.post(
        reverse("api_v1:cases:case-status", args=[case.id]),
        data=json.dumps({"status": Case.Statuses.CLOSED}),
        content_type="application/json",
    )
    assert close_response.status_code == 200

    case.status = Case.Statuses.CLOSED
    case.save(update_fields=["status"])
    client.force_login(admin)
    invalid_admin_response = client.post(
        reverse("api_v1:cases:case-status", args=[case.id]),
        data=json.dumps({"status": Case.Statuses.OPEN}),
        content_type="application/json",
    )
    assert invalid_admin_response.status_code == 400
    assert invalid_admin_response.json() == {"status": ["Invalid status transition for this case."]}

    case.status = Case.Statuses.WAITING_PROFESSIONAL
    case.save(update_fields=["status"])
    client.force_login(professional)
    invalid_professional_response = client.post(
        reverse("api_v1:cases:case-status", args=[case.id]),
        data=json.dumps({"status": Case.Statuses.CANCELLED}),
        content_type="application/json",
    )
    assert invalid_professional_response.status_code == 400
    assert invalid_professional_response.json() == {"status": ["Professionals cannot set this case status."]}


@pytest.mark.django_db
def test_delete_is_not_allowed_for_properties_assets_and_cases(client):
    user = User.objects.create_user(email="customer@example.com", password="Password123!")
    client.force_login(user)
    category = Category.objects.create(name="Clima", slug="clima")
    property_obj = Property.objects.create(owner_user=user, name="Casa")
    asset = Asset.objects.create(property=property_obj, category=category, name="Climatizzatore")
    case = Case.objects.create(customer_user=user, category=category, property=property_obj, asset=asset, title="Guasto")

    assert client.delete(reverse("api_v1:cases:property-detail", args=[property_obj.id])).status_code == 405
    assert client.delete(reverse("api_v1:cases:asset-detail", args=[asset.id])).status_code == 405
    assert client.delete(reverse("api_v1:cases:case-detail", args=[case.id])).status_code == 405


@pytest.mark.django_db
def test_case_permissions_and_write_guards(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    other_customer = User.objects.create_user(email="other@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    category = Category.objects.create(name="Clima", slug="clima")
    property_obj = Property.objects.create(owner_user=customer, name="Casa")
    asset = Asset.objects.create(property=property_obj, category=category, name="Split")
    case = Case.objects.create(
        customer_user=customer,
        assigned_professional=professional,
        category=category,
        property=property_obj,
        asset=asset,
        title="Clima guasto",
    )

    client.force_login(other_customer)
    assert client.get(reverse("api_v1:cases:case-detail", args=[case.id])).status_code == 404
    assert client.get(reverse("api_v1:cases:property-detail", args=[property_obj.id])).status_code == 404

    client.force_login(professional)
    response = client.patch(
        reverse("api_v1:cases:case-detail", args=[case.id]),
        data=json.dumps({"title": "Titolo cambiato"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert "Professionals cannot update case details." in str(response.json())


@pytest.mark.django_db
def test_case_asset_sets_property_automatically_and_must_match_selected_property(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    client.force_login(customer)
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    property_obj = Property.objects.create(owner_user=customer, name="Casa")
    other_property = Property.objects.create(owner_user=customer, name="Garage")
    asset = Asset.objects.create(property=property_obj, category=category, name="Quadro")

    create_response = client.post(
        reverse("api_v1:cases:case-list"),
        data=json.dumps(
            {
                "category_id": category.id,
                "asset_id": asset.id,
                "title": "Scatta il salvavita",
                "description": "Solo con forno acceso",
            }
        ),
        content_type="application/json",
    )
    assert create_response.status_code == 201
    assert create_response.json()["property_id"] == property_obj.id

    invalid_response = client.post(
        reverse("api_v1:cases:case-list"),
        data=json.dumps(
            {
                "category_id": category.id,
                "property_id": other_property.id,
                "asset_id": asset.id,
                "title": "Caso incoerente",
            }
        ),
        content_type="application/json",
    )
    assert invalid_response.status_code == 400
    assert invalid_response.json() == {"asset_id": ["Asset does not belong to the selected property."]}


@pytest.mark.django_db
def test_case_status_and_troubleshooting_coherence_guards(client):
    admin = User.objects.create_user(email="admin@example.com", password="Password123!", role=User.Roles.ADMIN)
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    other_category = Category.objects.create(name="Idraulica", slug="idraulica")
    flow = DiagnosticFlow.objects.create(
        title="Salvavita abbassato",
        slug="salvavita-abbassato-hardening",
        category=category,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    wrong_flow = DiagnosticFlow.objects.create(
        title="Perdita acqua",
        slug="perdita-acqua-hardening",
        category=other_category,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    node = DiagnosticNode.objects.create(
        flow=flow,
        title="Il salvavita scatta subito?",
        node_type=DiagnosticNode.NodeTypes.QUESTION,
        is_entrypoint=True,
    )
    next_node = DiagnosticNode.objects.create(
        flow=flow,
        title="Serve professionista",
        node_type=DiagnosticNode.NodeTypes.ESCALATION,
        sort_order=2,
    )
    DiagnosticOption.objects.create(from_node=node, to_node=next_node, label="Si")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")

    client.force_login(customer)
    schedule_response = client.post(
        reverse("api_v1:cases:case-status", args=[case.id]),
        data=json.dumps({"status": Case.Statuses.SCHEDULED}),
        content_type="application/json",
    )
    assert schedule_response.status_code == 400
    assert schedule_response.json() == {"status": ["A case must be assigned before it can be scheduled."]}

    wrong_flow_response = client.post(
        reverse("api_v1:cases:case-troubleshooting-start", args=[case.id]),
        data=json.dumps({"flow_id": wrong_flow.id}),
        content_type="application/json",
    )
    assert wrong_flow_response.status_code == 400
    assert wrong_flow_response.json() == {"flow_id": ["Flow category does not match the case category."]}

    client.force_login(admin)
    client.post(
        reverse("api_v1:cases:case-assign", args=[case.id]),
        data=json.dumps({"professional_user_id": professional.id}),
        content_type="application/json",
    )

    client.force_login(customer)
    start_response = client.post(
        reverse("api_v1:cases:case-troubleshooting-start", args=[case.id]),
        data=json.dumps({"flow_id": flow.id}),
        content_type="application/json",
    )
    assert start_response.status_code == 200

    wrong_node_response = client.post(
        reverse("api_v1:cases:case-troubleshooting-progress", args=[case.id]),
        data=json.dumps({"node_id": next_node.id}),
        content_type="application/json",
    )
    assert wrong_node_response.status_code == 400
    assert wrong_node_response.json() == {"node_id": ["Node does not match the current troubleshooting position."]}

    progress_without_option_response = client.post(
        reverse("api_v1:cases:case-troubleshooting-progress", args=[case.id]),
        data=json.dumps({"node_id": node.id}),
        content_type="application/json",
    )
    assert progress_without_option_response.status_code == 400
    assert progress_without_option_response.json() == {"option_id": ["Option is required for this node."]}

    client.post(
        reverse("api_v1:cases:case-status", args=[case.id]),
        data=json.dumps({"status": Case.Statuses.CANCELLED}),
        content_type="application/json",
    )
    terminal_response = client.post(
        reverse("api_v1:cases:case-troubleshooting-start", args=[case.id]),
        data=json.dumps({"flow_id": flow.id}),
        content_type="application/json",
    )
    assert terminal_response.status_code == 400
    assert terminal_response.json() == {"flow_id": ["Troubleshooting cannot be started on a terminal case."]}
