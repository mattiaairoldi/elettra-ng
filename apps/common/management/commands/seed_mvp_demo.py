from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.management import BaseCommand, call_command
from django.utils import timezone

from apps.cases.events import create_case_event
from apps.cases.models import Asset, Case, CaseEvent, CaseShareRequest, Property
from apps.organizations.models import Organization, OrganizationMembership, OrganizationPlan
from apps.organizations.services import get_or_create_builtin_plan, get_or_create_personal_organization
from apps.professionals.models import ProfessionalProfile
from apps.taxonomy.models import Category
from apps.troubleshooting.models import DiagnosticChapter


User = get_user_model()


CATEGORIES = [
    ("elettricita", "Elettricita"),
    ("elettrodomestici", "Elettrodomestici"),
    ("idraulica", "Idraulica"),
    ("climatizzazione", "Climatizzazione"),
    ("domotica", "Domotica"),
    ("sicurezza-domestica", "Sicurezza domestica"),
    ("manutenzione-generale", "Manutenzione generale"),
]

CHAPTER_CATEGORY_SLUGS = {
    "problemi-elettrici": "elettricita",
    "elettrodomestici": "elettrodomestici",
    "idraulica": "idraulica",
    "climatizzazione": "climatizzazione",
    "domotica": "domotica",
    "sicurezza-domestica": "sicurezza-domestica",
    "manutenzione-generale": "manutenzione-generale",
}


class Command(BaseCommand):
    help = "Seed repeatable local data for the MVP demo flow."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="Password123!",
            help="Password assigned to demo users.",
        )

    def handle(self, *args, **options):
        password = options["password"]

        categories = self.seed_categories()
        call_command("seed_diagnostic_chapters", verbosity=0)
        self.link_chapters_to_categories(categories)

        customer = self.get_or_create_user(
            email="demo.customer@example.com",
            password=password,
            role=User.Roles.CUSTOMER,
            first_name="Demo",
            last_name="Cliente",
        )
        professional = self.get_or_create_user(
            email="demo.pro@example.com",
            password=password,
            role=User.Roles.PROFESSIONAL,
            first_name="Demo",
            last_name="Tecnico",
        )

        personal_organization = get_or_create_personal_organization(customer)
        professional_organization = self.get_or_create_professional_organization(professional)
        profile = self.get_or_create_professional_profile(professional, categories)

        property_obj = self.get_or_create_property(customer, personal_organization)
        asset = self.get_or_create_asset(property_obj, categories["elettricita"])
        case = self.get_or_create_case(customer, property_obj, asset, categories["elettricita"])
        share_request = self.get_or_create_share_request(case, customer, professional_organization)

        self.stdout.write(self.style.SUCCESS("MVP demo data ready."))
        self.stdout.write("")
        self.stdout.write("Demo credentials:")
        self.stdout.write(f"  customer: demo.customer@example.com / {password}")
        self.stdout.write(f"  professional: demo.pro@example.com / {password}")
        self.stdout.write("")
        self.stdout.write("Demo objects:")
        self.stdout.write(f"  customer organization id: {personal_organization.id}")
        self.stdout.write(f"  professional organization id: {professional_organization.id}")
        self.stdout.write(f"  professional profile id: {profile.id}")
        self.stdout.write(f"  property id: {property_obj.id}")
        self.stdout.write(f"  asset id: {asset.id}")
        self.stdout.write(f"  case id: {case.id}")
        self.stdout.write(f"  share request id: {share_request.id}")

    def seed_categories(self):
        categories = {}
        for sort_order, (slug, name) in enumerate(CATEGORIES, start=10):
            category, _created = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "description": f"Categoria demo per {name.lower()}.",
                    "is_active": True,
                    "sort_order": sort_order,
                },
            )
            categories[slug] = category
        return categories

    def link_chapters_to_categories(self, categories):
        for chapter_slug, category_slug in CHAPTER_CATEGORY_SLUGS.items():
            DiagnosticChapter.objects.filter(slug=chapter_slug).update(category=categories[category_slug])

    def get_or_create_user(self, *, email, password, role, first_name, last_name):
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "email_verified": True,
                "is_active": True,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        else:
            update_fields = []
            for field, value in {
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "email_verified": True,
                "is_active": True,
            }.items():
                if getattr(user, field) != value:
                    setattr(user, field, value)
                    update_fields.append(field)
            if update_fields:
                update_fields.append("updated_at")
                user.save(update_fields=update_fields)
        return user

    def get_or_create_professional_organization(self, professional):
        plan = get_or_create_builtin_plan(OrganizationPlan.Kinds.PROFESSIONAL)
        organization, _created = Organization.objects.update_or_create(
            name="Demo Impianti Rossi",
            defaults={
                "kind": Organization.Kinds.PROFESSIONAL,
                "plan": plan,
                "status": Organization.Statuses.ACTIVE,
                "created_by_user": professional,
            },
        )
        OrganizationMembership.objects.update_or_create(
            user=professional,
            organization=organization,
            defaults={
                "role": OrganizationMembership.Roles.OWNER,
                "scope": OrganizationMembership.Scopes.ORGANIZATION,
                "status": OrganizationMembership.Statuses.ACTIVE,
                "approved_by_user": professional,
                "approved_at": timezone.now(),
            },
        )
        return organization

    def get_or_create_professional_profile(self, professional, categories):
        profile, _created = ProfessionalProfile.objects.update_or_create(
            user=professional,
            defaults={
                "display_name": "Demo Impianti Rossi",
                "bio": "Elettricista e manutentore demo per test MVP.",
                "phone": "+39 020000000",
                "email_public": "demo.pro@example.com",
                "is_available": True,
                "service_area_text": "Milano e provincia",
                "location": Point(9.19, 45.4642, srid=4326),
            },
        )
        profile.categories.set(
            [
                categories["elettricita"],
                categories["idraulica"],
                categories["climatizzazione"],
            ]
        )
        return profile

    def get_or_create_property(self, customer, organization):
        property_obj, _created = Property.objects.update_or_create(
            owner_user=customer,
            organization=organization,
            name="Casa Demo Milano",
            defaults={
                "address_text": "Via Demo 1",
                "city": "Milano",
                "location": Point(9.19, 45.4642, srid=4326),
                "notes": "Immobile demo per validazione MVP.",
            },
        )
        return property_obj

    def get_or_create_asset(self, property_obj, category):
        asset, _created = Asset.objects.update_or_create(
            property=property_obj,
            name="Quadro elettrico demo",
            defaults={
                "category": category,
                "description": "Quadro elettrico dell'ingresso.",
                "location_text": "Ingresso",
                "location": Point(9.1905, 45.4643, srid=4326),
                "metadata_json": {"demo": True},
            },
        )
        return asset

    def get_or_create_case(self, customer, property_obj, asset, category):
        case, created = Case.objects.update_or_create(
            customer_user=customer,
            title="Odore vicino al quadro elettrico",
            defaults={
                "owner_organization": property_obj.organization,
                "category": category,
                "property": property_obj,
                "asset": asset,
                "description": "L'utente sente odore di bruciato vicino al quadro elettrico.",
                "status": Case.Statuses.OPEN,
                "priority": Case.Priorities.HIGH,
                "source": Case.Sources.MANUAL,
            },
        )
        if created:
            create_case_event(
                case=case,
                event_type=CaseEvent.EventTypes.CASE_CREATED,
                actor_user=customer,
                payload={"status": case.status, "source": case.source, "demo": True},
            )
        return case

    def get_or_create_share_request(self, case, customer, professional_organization):
        share_request, created = CaseShareRequest.objects.update_or_create(
            case=case,
            requester_user=customer,
            recipient_organization=professional_organization,
            defaults={
                "recipient_membership": professional_organization.memberships.filter(
                    status=OrganizationMembership.Statuses.ACTIVE,
                ).first(),
                "status": CaseShareRequest.Statuses.PENDING,
                "share_scope": CaseShareRequest.ShareScopes.SUMMARY,
                "visible_title": case.title,
                "visible_summary": (
                    "Caso demo: odore di bruciato vicino al quadro elettrico. "
                    "Informazioni condivise in forma sintetica."
                ),
                "shared_payload_json": {
                    "demo": True,
                    "case_id": case.id,
                    "category": case.category.name,
                    "property_city": case.property.city if case.property_id else "",
                },
            },
        )
        if created:
            create_case_event(
                case=case,
                event_type=CaseEvent.EventTypes.CASE_SHARE_REQUEST_CREATED,
                actor_user=customer,
                payload={
                    "share_request_id": share_request.id,
                    "recipient_organization_id": professional_organization.id,
                    "share_scope": share_request.share_scope,
                    "demo": True,
                },
            )
        return share_request
