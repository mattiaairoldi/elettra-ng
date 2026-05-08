import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from apps.ai_assistant.admin import AiMessageAdmin
from apps.ai_assistant.models import AiMessage, AiSession
from apps.cases.admin import CaseEventAdmin
from apps.cases.models import Case, CaseEvent
from apps.taxonomy.models import Category
from apps.troubleshooting.models import DiagnosticFlow, DiagnosticNode, DiagnosticOption

User = get_user_model()


@pytest.mark.django_db
def test_troubleshooting_models_prevent_multiple_entrypoints_and_cross_flow_options():
    category = Category.objects.create(name="Elettricita", slug="elettricita-admin")
    flow_a = DiagnosticFlow.objects.create(
        title="Flow A",
        slug="flow-a-admin",
        category=category,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    flow_b = DiagnosticFlow.objects.create(
        title="Flow B",
        slug="flow-b-admin",
        category=category,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    entry_a = DiagnosticNode.objects.create(
        flow=flow_a,
        title="Entrypoint A",
        node_type=DiagnosticNode.NodeTypes.QUESTION,
        is_entrypoint=True,
    )
    other_node_a = DiagnosticNode.objects.create(
        flow=flow_a,
        title="Altro nodo A",
        node_type=DiagnosticNode.NodeTypes.SOLUTION,
    )
    other_node_b = DiagnosticNode.objects.create(
        flow=flow_b,
        title="Nodo B",
        node_type=DiagnosticNode.NodeTypes.SOLUTION,
    )

    with pytest.raises(ValidationError) as second_entrypoint_exc:
        DiagnosticNode.objects.create(
            flow=flow_a,
            title="Entrypoint duplicato",
            node_type=DiagnosticNode.NodeTypes.QUESTION,
            is_entrypoint=True,
        )
    assert "is_entrypoint" in second_entrypoint_exc.value.message_dict

    with pytest.raises(ValidationError) as cross_flow_option_exc:
        DiagnosticOption.objects.create(
            from_node=entry_a,
            to_node=other_node_b,
            label="Vai al flow sbagliato",
        )
    assert "to_node" in cross_flow_option_exc.value.message_dict

    valid_option = DiagnosticOption.objects.create(
        from_node=entry_a,
        to_node=other_node_a,
        label="Vai al nodo corretto",
    )
    assert valid_option.id is not None


@pytest.mark.django_db
def test_case_event_and_ai_message_admin_are_read_only():
    admin_site = AdminSite()
    case_event_admin = CaseEventAdmin(CaseEvent, admin_site)
    ai_message_admin = AiMessageAdmin(AiMessage, admin_site)

    admin_user = User.objects.create_user(
        email="admin@example.com",
        password="Password123!",
        role=User.Roles.ADMIN,
        is_staff=True,
        is_superuser=True,
    )
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Clima", slug="clima-admin")
    case = Case.objects.create(customer_user=customer, category=category, title="Caso admin")
    case_event = CaseEvent.objects.create(case=case, event_type=CaseEvent.EventTypes.CASE_CREATED, actor_user=customer)
    ai_session = AiSession.objects.create(user=customer, case=case)
    ai_message = AiMessage.objects.create(session=ai_session, role=AiMessage.Roles.ASSISTANT, content="ciao")

    request = type("Request", (), {"user": admin_user})()

    assert case_event_admin.has_add_permission(request) is False
    assert case_event_admin.has_change_permission(request, case_event) is False
    assert case_event_admin.has_delete_permission(request, case_event) is False

    assert ai_message_admin.has_add_permission(request) is False
    assert ai_message_admin.has_change_permission(request, ai_message) is False
    assert ai_message_admin.has_delete_permission(request, ai_message) is False
