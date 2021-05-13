# Generated by Django 3.2.2 on 2021-05-11 21:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('geodata', '0014_remove_collection_user'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='collectionmembership',
            new_name='collectionpermission',
        ),
        migrations.AlterField(
            model_name='collectionpermission',
            name='collection',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='collection_permissions',
                to='geodata.collection',
            ),
        ),
        migrations.AlterField(
            model_name='collectionpermission',
            name='user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='collection_permissions',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterModelOptions(
            name='collectionpermission',
            options={'default_related_name': 'collection_permissions'},
        ),
    ]