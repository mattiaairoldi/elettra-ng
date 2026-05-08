from django.contrib.gis.db import models as gis_models
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("common", "0001_enable_postgis"),
        ("cases", "0002_alter_caseevent_event_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="location",
            field=gis_models.PointField(blank=True, geography=True, null=True, srid=4326),
        ),
        migrations.AddField(
            model_name="asset",
            name="location",
            field=gis_models.PointField(blank=True, geography=True, null=True, srid=4326),
        ),
    ]
