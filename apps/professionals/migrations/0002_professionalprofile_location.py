from django.contrib.gis.db import models as gis_models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0001_enable_postgis"),
        ("professionals", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="professionalprofile",
            name="location",
            field=gis_models.PointField(blank=True, geography=True, null=True, srid=4326),
        ),
    ]
