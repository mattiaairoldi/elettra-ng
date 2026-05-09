from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.attachments.models import Attachment
from apps.cases.models import Asset, AssetMaintenanceEvent, AssetMaintenanceReminder, Case, CaseShareRequest, Property
from apps.organizations.models import Organization, OrganizationMembership
from apps.professionals.models import ProfessionalProfile
from apps.taxonomy.models import Category
from apps.troubleshooting.models import DiagnosticAdviceStep, DiagnosticChapter


User = get_user_model()


@pytest.mark.django_db
def test_seed_mvp_demo_creates_repeatable_demo_data():
    out = StringIO()
    call_command("seed_mvp_demo", stdout=out)
    call_command("seed_mvp_demo", stdout=StringIO())

    assert "MVP demo data ready." in out.getvalue()
    assert User.objects.filter(email="demo.customer@example.com", role=User.Roles.CUSTOMER).count() == 1
    assert User.objects.filter(email="demo.pro@example.com", role=User.Roles.PROFESSIONAL).count() == 1

    assert Category.objects.filter(slug="elettricita", is_active=True).exists()
    assert DiagnosticChapter.objects.filter(
        slug="problemi-elettrici",
        category__slug="elettricita",
        is_public=True,
    ).exists()
    assert DiagnosticAdviceStep.objects.filter(chapter__slug="problemi-elettrici").exists()

    professional = User.objects.get(email="demo.pro@example.com")
    professional_organization = Organization.objects.get(name="Demo Impianti Rossi")
    assert OrganizationMembership.objects.filter(
        user=professional,
        organization=professional_organization,
        status=OrganizationMembership.Statuses.ACTIVE,
    ).exists()
    assert ProfessionalProfile.objects.get(user=professional).categories.filter(slug="elettricita").exists()

    customer = User.objects.get(email="demo.customer@example.com")
    property_obj = Property.objects.get(owner_user=customer, name="Casa Demo Milano")
    asset = Asset.objects.get(property=property_obj, name="Quadro elettrico demo")
    appliance_asset = Asset.objects.get(property=property_obj, name="Lavatrice demo")
    assert appliance_asset.metadata_json["manufacturer"] == "DemoWash"
    assert Attachment.objects.filter(asset=appliance_asset, file_name="manuale-lavatrice-demo.pdf").exists()
    assert AssetMaintenanceEvent.objects.filter(
        asset=appliance_asset,
        event_type=AssetMaintenanceEvent.EventTypes.CLEANING,
        title="Pulizia filtro lavatrice",
    ).exists()
    assert AssetMaintenanceReminder.objects.filter(
        asset=appliance_asset,
        recurrence_rule=AssetMaintenanceReminder.RecurrenceRules.QUARTERLY,
        status=AssetMaintenanceReminder.Statuses.ACTIVE,
        title="Prossima pulizia filtro lavatrice",
    ).exists()
    case = Case.objects.get(customer_user=customer, title="Odore vicino al quadro elettrico")
    assert case.property_id == property_obj.id
    assert case.asset_id == asset.id
    assert case.category.slug == "elettricita"

    share_request = CaseShareRequest.objects.get(case=case, recipient_organization=professional_organization)
    assert share_request.status == CaseShareRequest.Statuses.PENDING
    assert share_request.share_scope == CaseShareRequest.ShareScopes.SUMMARY

    assert User.objects.filter(email="demo.customer@example.com").count() == 1
    assert Asset.objects.filter(property=property_obj, name="Lavatrice demo").count() == 1
    assert Case.objects.filter(customer_user=customer, title="Odore vicino al quadro elettrico").count() == 1
    assert CaseShareRequest.objects.filter(case=case, recipient_organization=professional_organization).count() == 1
