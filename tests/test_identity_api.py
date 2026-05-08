import json

import pytest
from django.core import mail
from django.test import override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.identity.tokens import generate_email_verification_token, generate_password_reset_token

User = get_user_model()


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
def test_register_endpoint_creates_customer_user_and_sends_email(client):
    response = client.post(
        reverse("api_v1:auth:register"),
        data=json.dumps({
            "email": "mario@example.com",
            "password": "Password123!",
            "first_name": "Mario",
            "last_name": "Rossi",
        }),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "mario@example.com"
    assert body["user"]["role"] == "customer"
    assert "verification_token" not in body
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["mario@example.com"]
    assert "verify your email" in mail.outbox[0].subject.lower()
    assert User.objects.filter(email="mario@example.com").exists()


@pytest.mark.django_db
def test_login_me_and_logout_flow(client):
    user = User.objects.create_user(
        email="user@example.com",
        password="Password123!",
        first_name="Mario",
        last_name="Rossi",
    )

    login_response = client.post(
        reverse("api_v1:auth:login"),
        data=json.dumps({"email": "user@example.com", "password": "Password123!"}),
        content_type="application/json",
    )

    assert login_response.status_code == 200
    assert login_response.json()["user"]["email"] == user.email

    me_response = client.get(reverse("api_v1:auth:me"))
    assert me_response.status_code == 200
    assert me_response.json()["user"]["email"] == user.email

    logout_response = client.post(reverse("api_v1:auth:logout"))
    assert logout_response.status_code == 204

    me_after_logout_response = client.get(reverse("api_v1:auth:me"))
    assert me_after_logout_response.status_code == 403


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
def test_forgot_password_and_reset_password_flow(client):
    user = User.objects.create_user(email="user@example.com", password="Password123!")

    forgot_response = client.post(
        reverse("api_v1:auth:forgot-password"),
        data=json.dumps({"email": user.email}),
        content_type="application/json",
    )

    assert forgot_response.status_code == 202
    assert "reset_token" not in forgot_response.json()
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [user.email]
    reset_token = generate_password_reset_token(user.email)

    reset_response = client.post(
        reverse("api_v1:auth:reset-password"),
        data=json.dumps({"token": reset_token, "new_password": "NewPassword123!"}),
        content_type="application/json",
    )

    assert reset_response.status_code == 200
    user.refresh_from_db()
    assert user.check_password("NewPassword123!")


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
def test_register_endpoint_dispatches_email_through_celery_task(client, monkeypatch):
    call_log = []

    from apps.identity import views

    original_delay = views.send_verification_email_task.delay

    def tracked_delay(user_id):
        call_log.append(user_id)
        return original_delay(user_id)

    monkeypatch.setattr(views.send_verification_email_task, "delay", tracked_delay)

    response = client.post(
        reverse("api_v1:auth:register"),
        data=json.dumps(
            {
                "email": "celery-register@example.com",
                "password": "Password123!",
                "first_name": "Celery",
                "last_name": "Register",
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 201
    assert len(call_log) == 1
    assert len(mail.outbox) == 1


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)
def test_forgot_password_endpoint_dispatches_email_through_celery_task(client, monkeypatch):
    user = User.objects.create_user(email="celery-reset@example.com", password="Password123!")
    call_log = []

    from apps.identity import views

    original_delay = views.send_password_reset_email_task.delay

    def tracked_delay(user_id):
        call_log.append(user_id)
        return original_delay(user_id)

    monkeypatch.setattr(views.send_password_reset_email_task, "delay", tracked_delay)

    response = client.post(
        reverse("api_v1:auth:forgot-password"),
        data=json.dumps({"email": user.email}),
        content_type="application/json",
    )

    assert response.status_code == 202
    assert call_log == [user.id]
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_verify_email_marks_user_as_verified(client):
    user = User.objects.create_user(email="user@example.com", password="Password123!")
    token = generate_email_verification_token(user.email)

    response = client.post(
        reverse("api_v1:auth:verify-email"),
        data=json.dumps({"token": token}),
        content_type="application/json",
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.email_verified is True
