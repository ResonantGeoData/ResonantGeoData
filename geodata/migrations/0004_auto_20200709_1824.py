# Generated by Django 3.0.7 on 2020-07-09 18:24

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geodata', '0003_geometryarchive_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='rasterentry',
            name='data_mask',
            field=django.contrib.gis.db.models.fields.PolygonField(null=True, srid=4326),
        ),
        migrations.AddField(
            model_name='rasterfile', name='checksum', field=models.TextField(blank=True, null=True),
        ),
    ]
