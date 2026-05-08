import pytest

from apps.identity.models import User


@pytest.mark.django_db
def test_create_user_defaults_to_customer_role():
    user = User.objects.create_user(email="user@example.com", password="password123")

    assert user.role == User.Roles.CUSTOMER
    assert user.username == "user@example.com"
