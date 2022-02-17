# Generated by Django 3.2.9 on 2021-12-07 02:53

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import rgd.models.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('rgd', '0005_auto_20211105_1715'),
        ('rgd_3d', '0004_auto_20211116_1814'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tiles3D',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('failure_reason', models.TextField(null=True)),
                (
                    'status',
                    models.CharField(
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
                (
                    'created',
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name='modified'
                    ),
                ),
                ('name', models.CharField(blank=True, max_length=1000)),
                ('description', models.TextField(blank=True, null=True)),
                (
                    'json_file',
                    models.ForeignKey(
                        help_text='The `tileset.json` file that contains metadata about this set of 3D tiles.',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='+',
                        to='rgd.checksumfile',
                    ),
                ),
            ],
            options={
                'verbose_name': '3D tiles',
                'verbose_name_plural': '3D tiles',
            },
            bases=(
                models.Model,
                rgd.models.mixins.PermissionPathMixin,
                rgd.models.mixins.DetailViewMixin,
            ),
        ),
        migrations.CreateModel(
            name='Tiles3DMeta',
            fields=[
                (
                    'spatialentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='rgd.spatialentry',
                    ),
                ),
                (
                    'created',
                    django_extensions.db.fields.CreationDateTimeField(
                        auto_now_add=True, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    django_extensions.db.fields.ModificationDateTimeField(
                        auto_now=True, verbose_name='modified'
                    ),
                ),
                (
                    'source',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to='rgd_3d.tiles3d'
                    ),
                ),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
            bases=('rgd.spatialentry', models.Model, rgd.models.mixins.PermissionPathMixin),
        ),
    ]
