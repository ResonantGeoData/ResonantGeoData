# Generated by Django 3.0.7 on 2020-07-28 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('geodata', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='convertedimagefile',
            name='last_validation',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='geometryarchive',
            name='last_validation',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='imagefile', name='last_validation', field=models.BooleanField(default=True),
        ),
    ]
