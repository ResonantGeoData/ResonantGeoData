# Generated by Django 3.2.7 on 2021-09-27 15:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rgd_geometry', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='geometryarchive',
            name='status',
            field=models.CharField(
                choices=[
                    ('created', 'Created but not queued'),
                    ('queued', 'Queued for processing'),
                    ('running', 'Processing'),
                    ('failed', 'Failed'),
                    ('success', 'Succeeded'),
                    ('skipped', 'Skipped'),
                ],
                default='created',
                max_length=20,
            ),
        ),
    ]
