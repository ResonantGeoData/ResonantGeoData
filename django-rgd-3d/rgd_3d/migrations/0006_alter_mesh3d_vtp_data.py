# Generated by Django 4.0.4 on 2022-04-13 16:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rgd', '0009_alter_checksumfile_collection_and_more'),
        ('rgd_3d', '0005_tiles3d_tiles3dmeta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mesh3d',
            name='vtp_data',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='rgd.checksumfile',
            ),
        ),
    ]
