from django.contrib.gis.db import models


class ProfessionalProfile(models.Model):
    user = models.OneToOneField("identity.User", on_delete=models.CASCADE, related_name="professional_profile")
    display_name = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email_public = models.EmailField(blank=True)
    is_available = models.BooleanField(default=True)
    service_area_text = models.CharField(max_length=255, blank=True)
    location = models.PointField(srid=4326, geography=True, null=True, blank=True)
    categories = models.ManyToManyField("taxonomy.Category", related_name="professional_profiles", blank=True)
    tags = models.ManyToManyField("taxonomy.Tag", related_name="professional_profiles", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_name", "id")

    def __str__(self):
        return self.display_name
