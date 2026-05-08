from django.db import models


class Appointment(models.Model):
    class Statuses(models.TextChoices):
        REQUESTED = "requested", "Requested"
        CONFIRMED = "confirmed", "Confirmed"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        RESCHEDULED = "rescheduled", "Rescheduled"

    case = models.ForeignKey("cases.Case", on_delete=models.CASCADE, related_name="appointments")
    professional_profile = models.ForeignKey(
        "professionals.ProfessionalProfile",
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    scheduled_start_at = models.DateTimeField()
    scheduled_end_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Statuses.choices, default=Statuses.REQUESTED)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("scheduled_start_at", "id")
