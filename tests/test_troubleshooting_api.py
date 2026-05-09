import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.cases.models import Case, CaseEvent
from apps.taxonomy.models import Category
from apps.troubleshooting.models import (
    DiagnosticAdviceStep,
    DiagnosticChapter,
    DiagnosticChapterOption,
    DiagnosticFlow,
    DiagnosticNode,
    DiagnosticOption,
    DiagnosticSafetyRule,
)

User = get_user_model()


@pytest.mark.django_db
def test_diagnostic_chapters_list_returns_public_published_chapters_with_options_and_safety_rules(client):
    public_chapter = DiagnosticChapter.objects.create(
        name="Problemi elettrici",
        slug="problemi-elettrici",
        status=DiagnosticChapter.Statuses.PUBLISHED,
        is_public=True,
        prompt_context="Ambito elettrico domestico.",
        safety_context="Non suggerire lavori elettrici rischiosi.",
    )
    option = DiagnosticChapterOption.objects.create(
        chapter=public_chapter,
        label="Salvavita",
        slug="salvavita",
        option_type=DiagnosticChapterOption.OptionTypes.ASSET_TYPE,
    )
    DiagnosticSafetyRule.objects.create(
        chapter=public_chapter,
        title="Odore di bruciato",
        trigger_terms_json=["odore di bruciato"],
        risk_level=DiagnosticSafetyRule.RiskLevels.URGENT,
        escalation_level=DiagnosticSafetyRule.EscalationLevels.URGENT,
    )
    DiagnosticChapter.objects.create(
        name="Bozza",
        slug="bozza",
        status=DiagnosticChapter.Statuses.DRAFT,
        is_public=True,
    )

    response = client.get(reverse("api_v1:troubleshooting:chapter-list"))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [public_chapter.id]
    assert response.json()[0]["options"][0]["id"] == option.id
    assert response.json()[0]["safety_rules"][0]["risk_level"] == "urgent"


@pytest.mark.django_db
def test_diagnostic_chapters_support_search_category_and_options_endpoint(client):
    electricity = Category.objects.create(name="Elettricita", slug="elettricita-chapters")
    public_chapter = DiagnosticChapter.objects.create(
        name="Problemi elettrici",
        slug="problemi-elettrici",
        category=electricity,
        status=DiagnosticChapter.Statuses.PUBLISHED,
        is_public=True,
    )
    option = DiagnosticChapterOption.objects.create(
        chapter=public_chapter,
        label="Presa",
        slug="presa",
        option_type=DiagnosticChapterOption.OptionTypes.ASSET_TYPE,
    )

    category_response = client.get(
        reverse("api_v1:troubleshooting:chapter-list"),
        {"category_id": electricity.id},
    )
    assert category_response.status_code == 200
    assert [item["slug"] for item in category_response.json()] == ["problemi-elettrici"]

    search_response = client.get(reverse("api_v1:troubleshooting:chapter-list"), {"q": "elettrici"})
    assert search_response.status_code == 200
    assert [item["id"] for item in search_response.json()] == [public_chapter.id]

    options_response = client.get(reverse("api_v1:troubleshooting:chapter-options", args=[public_chapter.id]))
    assert options_response.status_code == 200
    assert [item["id"] for item in options_response.json()] == [option.id]


@pytest.mark.django_db
def test_diagnostic_advice_steps_support_generic_and_option_specific_guidance(client):
    chapter = DiagnosticChapter.objects.create(
        name="Problemi elettrici",
        slug="problemi-elettrici-advice",
        status=DiagnosticChapter.Statuses.PUBLISHED,
        is_public=True,
    )
    option = DiagnosticChapterOption.objects.create(
        chapter=chapter,
        label="Presa",
        slug="presa",
        option_type=DiagnosticChapterOption.OptionTypes.ASSET_TYPE,
    )
    generic_step = DiagnosticAdviceStep.objects.create(
        chapter=chapter,
        title="Verifica sicura",
        slug="verifica-sicura",
        body="Osserva solo elementi esterni.",
        sort_order=10,
    )
    option_step = DiagnosticAdviceStep.objects.create(
        chapter=chapter,
        chapter_option=option,
        title="Controllo presa",
        slug="controllo-presa",
        body="Non smontare la presa.",
        sort_order=20,
    )
    other_option = DiagnosticChapterOption.objects.create(
        chapter=chapter,
        label="Luce",
        slug="luce",
    )
    DiagnosticAdviceStep.objects.create(
        chapter=chapter,
        chapter_option=other_option,
        title="Controllo luce",
        slug="controllo-luce",
        body="Controllo non pertinente.",
        sort_order=30,
    )

    response = client.get(
        reverse("api_v1:troubleshooting:chapter-advice-steps", args=[chapter.id]),
        {"option_id": option.id},
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [generic_step.id, option_step.id]
    assert response.json()[0]["resolution_prompt"] == "Hai risolto?"


@pytest.mark.django_db
def test_diagnostic_advice_feedback_updates_case_and_suggests_next_actions(client):
    customer = User.objects.create_user(email="customer@example.com", password="Password123!")
    category = Category.objects.create(name="Elettricita", slug="elettricita-advice-feedback")
    case = Case.objects.create(customer_user=customer, category=category, title="Presa non funziona")
    chapter = DiagnosticChapter.objects.create(
        name="Problemi elettrici",
        slug="problemi-elettrici-feedback",
        status=DiagnosticChapter.Statuses.PUBLISHED,
        is_public=True,
    )
    step = DiagnosticAdviceStep.objects.create(
        chapter=chapter,
        title="Verifica sicura",
        slug="verifica-sicura",
        body="Osserva solo elementi esterni.",
    )
    client.force_login(customer)

    response = client.post(
        reverse("api_v1:troubleshooting:advice-step-feedback", args=[step.id]),
        data=json.dumps({"case_id": case.id, "resolved": False, "note": "Non e' cambiato nulla"}),
        content_type="application/json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_status"] == Case.Statuses.IN_DIAGNOSIS
    assert [item["code"] for item in payload["next_actions"]] == [
        "continue_guided",
        "start_ai_diagnostic",
        "share_with_professional",
    ]
    case.refresh_from_db()
    assert case.status == Case.Statuses.IN_DIAGNOSIS
    progress_event = CaseEvent.objects.get(case=case, event_type=CaseEvent.EventTypes.TROUBLESHOOTING_PROGRESS)
    assert progress_event.payload_json["diagnostic_advice_step_id"] == step.id
    assert progress_event.payload_json["resolved"] is False


@pytest.mark.django_db
def test_diagnostic_advice_feedback_can_resolve_case(client):
    customer = User.objects.create_user(email="customer-resolved@example.com", password="Password123!")
    category = Category.objects.create(name="Idraulica", slug="idraulica-advice-feedback")
    case = Case.objects.create(customer_user=customer, category=category, title="Scarico lento")
    chapter = DiagnosticChapter.objects.create(
        name="Idraulica",
        slug="idraulica-feedback",
        status=DiagnosticChapter.Statuses.PUBLISHED,
        is_public=True,
    )
    step = DiagnosticAdviceStep.objects.create(
        chapter=chapter,
        title="Controllo scarico",
        slug="controllo-scarico",
        body="Verifica se l'acqua defluisce lentamente.",
    )
    client.force_login(customer)

    response = client.post(
        reverse("api_v1:troubleshooting:advice-step-feedback", args=[step.id]),
        data=json.dumps({"case_id": case.id, "resolved": True}),
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["case_status"] == Case.Statuses.RESOLVED
    assert response.json()["next_actions"] == []
    case.refresh_from_db()
    assert case.status == Case.Statuses.RESOLVED
    assert case.closed_at is not None


@pytest.mark.django_db
def test_flows_list_returns_only_public_published_flows(client):
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    public_flow = DiagnosticFlow.objects.create(
        title="Salvavita abbassato",
        slug="salvavita-abbassato",
        category=category,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    DiagnosticFlow.objects.create(
        title="Bozza interna",
        slug="bozza-interna",
        category=category,
        status=DiagnosticFlow.Statuses.DRAFT,
        is_public=True,
    )

    response = client.get(reverse("api_v1:troubleshooting:flow-list"))

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [public_flow.id]


@pytest.mark.django_db
def test_flows_list_supports_category_and_search_filters(client):
    electricity = Category.objects.create(name="Elettricita", slug="elettricita")
    climate = Category.objects.create(name="Clima", slug="clima")
    matching_flow = DiagnosticFlow.objects.create(
        title="Climatizzatore non raffredda",
        slug="clima-non-raffredda",
        category=climate,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    DiagnosticFlow.objects.create(
        title="Salvavita abbassato",
        slug="salvavita-abbassato",
        category=electricity,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )

    category_response = client.get(
        reverse("api_v1:troubleshooting:flow-list"),
        {"category_id": climate.id},
    )
    assert category_response.status_code == 200
    assert [item["id"] for item in category_response.json()] == [matching_flow.id]

    search_response = client.get(reverse("api_v1:troubleshooting:flow-list"), {"q": "raffredda"})
    assert search_response.status_code == 200
    assert [item["slug"] for item in search_response.json()] == ["clima-non-raffredda"]


@pytest.mark.django_db
def test_flow_detail_and_nodes_list_return_public_published_content(client):
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    flow = DiagnosticFlow.objects.create(
        title="Salvavita abbassato",
        slug="salvavita-abbassato",
        category=category,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    entry_node = DiagnosticNode.objects.create(
        flow=flow,
        title="Controlla il quadro",
        node_type=DiagnosticNode.NodeTypes.QUESTION,
        is_entrypoint=True,
        sort_order=1,
    )
    DiagnosticNode.objects.create(
        flow=flow,
        title="Ripristina il salvavita",
        node_type=DiagnosticNode.NodeTypes.SOLUTION,
        sort_order=2,
    )

    detail_response = client.get(reverse("api_v1:troubleshooting:flow-detail", args=[flow.id]))
    assert detail_response.status_code == 200
    assert detail_response.json()["slug"] == flow.slug

    nodes_response = client.get(reverse("api_v1:troubleshooting:flow-nodes", args=[flow.id]))
    assert nodes_response.status_code == 200
    assert nodes_response.json()[0]["id"] == entry_node.id


@pytest.mark.django_db
def test_node_detail_and_options_return_public_published_content(client):
    category = Category.objects.create(name="Elettricita", slug="elettricita")
    flow = DiagnosticFlow.objects.create(
        title="Salvavita abbassato",
        slug="salvavita-abbassato",
        category=category,
        status=DiagnosticFlow.Statuses.PUBLISHED,
        is_public=True,
    )
    from_node = DiagnosticNode.objects.create(
        flow=flow,
        title="Il salvavita scatta subito?",
        node_type=DiagnosticNode.NodeTypes.QUESTION,
        sort_order=1,
    )
    to_node = DiagnosticNode.objects.create(
        flow=flow,
        title="Serve un professionista",
        node_type=DiagnosticNode.NodeTypes.ESCALATION,
        sort_order=2,
    )
    option = DiagnosticOption.objects.create(
        from_node=from_node,
        to_node=to_node,
        label="Si, scatta subito",
        sort_order=1,
    )

    node_response = client.get(reverse("api_v1:troubleshooting:node-detail", args=[from_node.id]))
    assert node_response.status_code == 200
    assert node_response.json()["title"] == from_node.title

    options_response = client.get(reverse("api_v1:troubleshooting:node-options", args=[from_node.id]))
    assert options_response.status_code == 200
    assert options_response.json()[0]["id"] == option.id
