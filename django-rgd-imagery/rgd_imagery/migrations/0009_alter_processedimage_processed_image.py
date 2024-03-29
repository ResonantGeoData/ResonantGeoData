# Generated by Django 3.2.11 on 2022-02-01 17:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rgd_imagery', '0008_delete_kwcocoarchive'),
    ]

    operations = [
        migrations.AlterField(
            model_name='processedimage',
            name='processed_image',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='sourceprocessimage_set',
                to='rgd_imagery.image',
            ),
        ),
    ]
