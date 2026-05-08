from datetime import timedelta

import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.cases.models import Case
from apps.professionals.models import ProfessionalProfile
from apps.taxonomy.models import Category

User = get_user_model()


@pytest.mark.django_db
def test_appointment_create_list_and_detail(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional_user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_profile = ProfessionalProfile.objects.create(user=professional_user, display_name="Mario Rossi")
    category = Category.objects.create(name="Clima", slug="clima")
    case = Case.objects.create(customer_user=customer, category=category, title="Clima non raffredda")
    client.force_login(customer)

    create_response = client.post(
        reverse("api_v1:appointments:appointment-list"),
        data=json.dumps(
            {
                "case_id": case.id,
                "professional_profile_id": professional_profile.id,
                "scheduled_start_at": timezone.now().isoformat(),
                "notes": "Sopralluogo iniziale",
            }
        ),
        content_type="application/json",
    )
    assert create_response.status_code == 201
    appointment_id = create_response.json()["id"]

    list_response = client.get(reverse("api_v1:appointments:appointment-list"), {"case_id": case.id})
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [appointment_id]

    detail_response = client.get(reverse("api_v1:appointments:appointment-detail", args=[appointment_id]))
    assert detail_response.status_code == 200
    assert detail_response.json()["notes"] == "Sopralluogo iniziale"


@pytest.mark.django_db
def test_appointment_status_update(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional_user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_profile = ProfessionalProfile.objects.create(user=professional_user, display_name="Mario Rossi")
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    appointment = Appointment.objects.create(
        case=case,
        professional_profile=professional_profile,
        scheduled_start_at=timezone.now(),
    )
    client.force_login(professional_user)

    response = client.post(
        reverse("api_v1:appointments:appointment-status", args=[appointment.id]),
        data=json.dumps({"status": Appointment.Statuses.CONFIRMED}),
        content_type="application/json",
    )

    assert response.status_code == 200
    appointment.refresh_from_db()
    assert appointment.status == Appointment.Statuses.CONFIRMED


@pytest.mark.django_db
def test_customer_cannot_confirm_appointment_but_can_cancel_it(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional_user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_profile = ProfessionalProfile.objects.create(user=professional_user, display_name="Mario Rossi")
    category = Category.objects.create(name="Idraulica", slug="idraulica-appointment-role")
    case = Case.objects.create(
        customer_user=customer,
        assigned_professional=professional_user,
        category=category,
        title="Perdita acqua",
        status=Case.Statuses.WAITING_PROFESSIONAL,
    )
    appointment = Appointment.objects.create(
        case=case,
        professional_profile=professional_profile,
        scheduled_start_at=timezone.now(),
    )
    client.force_login(customer)

    confirm_response = client.post(
        reverse("api_v1:appointments:appointment-status", args=[appointment.id]),
        data=json.dumps({"status": Appointment.Statuses.CONFIRMED}),
        content_type="application/json",
    )
    assert confirm_response.status_code == 400
    assert confirm_response.json() == {"status": ["Customers can only cancel appointments."]}

    cancel_response = client.post(
        reverse("api_v1:appointments:appointment-status", args=[appointment.id]),
        data=json.dumps({"status": Appointment.Statuses.CANCELLED}),
        content_type="application/json",
    )
    assert cancel_response.status_code == 200
    appointment.refresh_from_db()
    assert appointment.status == Appointment.Statuses.CANCELLED


@pytest.mark.django_db
def test_delete_is_not_allowed_for_appointments(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional_user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_profile = ProfessionalProfile.objects.create(user=professional_user, display_name="Mario Rossi")
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    case = Case.objects.create(customer_user=customer, category=category, title="Salvavita abbassato")
    appointment = Appointment.objects.create(
        case=case,
        professional_profile=professional_profile,
        scheduled_start_at=timezone.now(),
    )
    client.force_login(customer)

    response = client.delete(reverse("api_v1:appointments:appointment-detail", args=[appointment.id]))

    assert response.status_code == 405


@pytest.mark.django_db
def test_appointment_requires_matching_assignment_and_valid_times(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    assigned_professional_user = User.objects.create_user(
        email="assigned@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    other_professional_user = User.objects.create_user(
        email="other-pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    assigned_profile = ProfessionalProfile.objects.create(user=assigned_professional_user, display_name="Mario Rossi")
    other_profile = ProfessionalProfile.objects.create(user=other_professional_user, display_name="Luigi Verdi")
    category = Category.objects.create(name="Clima", slug="clima-hardening")
    case = Case.objects.create(
        customer_user=customer,
        assigned_professional=assigned_professional_user,
        category=category,
        title="Clima non raffredda",
    )
    client.force_login(customer)

    mismatch_response = client.post(
        reverse("api_v1:appointments:appointment-list"),
        data=json.dumps(
            {
                "case_id": case.id,
                "professional_profile_id": other_profile.id,
                "scheduled_start_at": timezone.now().isoformat(),
                "notes": "Sopralluogo iniziale",
            }
        ),
        content_type="application/json",
    )
    assert mismatch_response.status_code == 400
    assert mismatch_response.json() == {
        "professional_profile_id": ["Professional profile does not match the case assignment."]
    }

    invalid_time_response = client.post(
        reverse("api_v1:appointments:appointment-list"),
        data=json.dumps(
            {
                "case_id": case.id,
                "professional_profile_id": assigned_profile.id,
                "scheduled_start_at": timezone.now().isoformat(),
                "scheduled_end_at": (timezone.now() - timedelta(hours=1)).isoformat(),
                "notes": "Orario incoerente",
            }
        ),
        content_type="application/json",
    )
    assert invalid_time_response.status_code == 400
    assert invalid_time_response.json() == {"scheduled_end_at": ["End time must be after start time."]}


@pytest.mark.django_db
def test_appointment_status_transitions_keep_case_status_coherent(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional_user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_profile = ProfessionalProfile.objects.create(user=professional_user, display_name="Mario Rossi")
    category = Category.objects.create(name="Elettricita", slug="elettricita-hardening")
    case = Case.objects.create(
        customer_user=customer,
        assigned_professional=professional_user,
        category=category,
        title="Salvavita abbassato",
        status=Case.Statuses.WAITING_PROFESSIONAL,
    )
    appointment = Appointment.objects.create(
        case=case,
        professional_profile=professional_profile,
        scheduled_start_at=timezone.now(),
    )
    client.force_login(professional_user)

    confirm_response = client.post(
        reverse("api_v1:appointments:appointment-status", args=[appointment.id]),
        data=json.dumps({"status": Appointment.Statuses.CONFIRMED}),
        content_type="application/json",
    )
    assert confirm_response.status_code == 200
    appointment.refresh_from_db()
    case.refresh_from_db()
    assert appointment.status == Appointment.Statuses.CONFIRMED
    assert case.status == Case.Statuses.SCHEDULED

    invalid_transition_response = client.post(
        reverse("api_v1:appointments:appointment-status", args=[appointment.id]),
        data=json.dumps({"status": Appointment.Statuses.REQUESTED}),
        content_type="application/json",
    )
    assert invalid_transition_response.status_code == 400
    assert invalid_transition_response.json() == {"status": ["Invalid status transition for this appointment."]}

    cancel_response = client.post(
        reverse("api_v1:appointments:appointment-status", args=[appointment.id]),
        data=json.dumps({"status": Appointment.Statuses.CANCELLED}),
        content_type="application/json",
    )
    assert cancel_response.status_code == 200
    appointment.refresh_from_db()
    case.refresh_from_db()
    assert appointment.status == Appointment.Statuses.CANCELLED
    assert case.status == Case.Statuses.WAITING_PROFESSIONAL


@pytest.mark.django_db
def test_appointment_partial_update_uses_existing_case_and_profile_and_terminal_appointments_are_locked(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    professional_user = User.objects.create_user(
        email="pro@example.com",
        password="Password123!",
        role=User.Roles.PROFESSIONAL,
    )
    professional_profile = ProfessionalProfile.objects.create(user=professional_user, display_name="Mario Rossi")
    category = Category.objects.create(name="Clima", slug="clima-appointment-patch")
    case = Case.objects.create(
        customer_user=customer,
        assigned_professional=professional_user,
        category=category,
        title="Clima non raffredda",
    )
    appointment = Appointment.objects.create(
        case=case,
        professional_profile=professional_profile,
        scheduled_start_at=timezone.now(),
        notes="Note iniziali",
    )
    client.force_login(customer)

    patch_response = client.patch(
        reverse("api_v1:appointments:appointment-detail", args=[appointment.id]),
        data=json.dumps({"notes": "Note aggiornate"}),
        content_type="application/json",
    )
    assert patch_response.status_code == 200
    appointment.refresh_from_db()
    assert appointment.notes == "Note aggiornate"

    appointment.status = Appointment.Statuses.COMPLETED
    appointment.save(update_fields=["status"])

    locked_response = client.patch(
        reverse("api_v1:appointments:appointment-detail", args=[appointment.id]),
        data=json.dumps({"notes": "Non dovrebbe passare"}),
        content_type="application/json",
    )
    assert locked_response.status_code == 400
    assert locked_response.json() == {"non_field_errors": ["Terminal appointments cannot be edited."]}
