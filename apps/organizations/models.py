from django.db import models


class OrganizationPlan(models.Model):
    class Kinds(models.TextChoices):
        PERSONAL = "personal", "Personal"
        PROFESSIONAL = "professional", "Professional"
        MANAGED = "managed", "Managed"
        HYBRID = "hybrid", "Hybrid"

    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=160)
    kind = models.CharField(max_length=32, choices=Kinds.choices)
    max_members = models.PositiveIntegerField(default=1)
    can_open_cases = models.BooleanField(default=False)
    can_manage_properties = models.BooleanField(default=False)
    can_share_cases = models.BooleanField(default=False)
    can_receive_cases = models.BooleanField(default=False)
    can_accept_case_requests = models.BooleanField(default=False)
    can_manage_members = models.BooleanField(default=False)
    can_manage_billing = models.BooleanField(default=False)
    can_view_all_org_cases = models.BooleanField(default=False)
    can_use_ai_diagnostics = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("slug",)

    def __str__(self):
        return self.name


class Organization(models.Model):
    class Kinds(models.TextChoices):
        PERSONAL = "personal", "Personal"
        PROFESSIONAL = "professional", "Professional"
        MANAGED = "managed", "Managed"
        HYBRID = "hybrid", "Hybrid"

    class Statuses(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        ARCHIVED = "archived", "Archived"

    name = models.CharField(max_length=200)
    kind = models.CharField(max_length=32, choices=Kinds.choices)
    plan = models.ForeignKey(OrganizationPlan, on_delete=models.PROTECT, related_name="organizations")
    status = models.CharField(max_length=32, choices=Statuses.choices, default=Statuses.ACTIVE)
    personal_owner = models.OneToOneField(
        "identity.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="personal_organization",
    )
    created_by_user = models.ForeignKey(
        "identity.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_organizations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name", "id")
        indexes = [
            models.Index(fields=("kind", "status"), name="org_kind_status_idx"),
        ]

    def __str__(self):
        return self.name


class OrganizationMembership(models.Model):
    class Roles(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Admin"
        ADMINISTRATIVE = "administrative", "Administrative"
        TECHNICIAN = "technician", "Technician"

    class Scopes(models.TextChoices):
        ORGANIZATION = "organization", "Organization"
        ASSIGNED = "assigned", "Assigned"

    class Statuses(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    user = models.ForeignKey("identity.User", on_delete=models.CASCADE, related_name="organization_memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=32, choices=Roles.choices)
    scope = models.CharField(max_length=32, choices=Scopes.choices, default=Scopes.ASSIGNED)
    status = models.CharField(max_length=32, choices=Statuses.choices, default=Statuses.PENDING)
    approved_by_user = models.ForeignKey(
        "identity.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_organization_memberships",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("organization__name", "user__email", "id")
        constraints = [
            models.UniqueConstraint(fields=("organization", "user"), name="unique_organization_membership_user"),
        ]
        indexes = [
            models.Index(fields=("organization", "status"), name="org_membership_org_status_idx"),
            models.Index(fields=("user", "status"), name="org_membership_user_status_idx"),
            models.Index(fields=("role", "scope"), name="org_membership_role_scope_idx"),
        ]

    def __str__(self):
        return f"{self.user} @ {self.organization}"
