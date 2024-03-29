# Generated by Django 3.2.6 on 2021-08-20 12:12

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import rgd.models.mixins


class Migration(migrations.Migration):

    dependencies = [
        ('rgd', '0002_alter_spatialasset_files'),
        ('rgd_imagery', '0003_remove_bandmeta_dtype'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcessedImage',
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
                (
                    'ancillary_files',
                    models.ManyToManyField(
                        blank=True,
                        related_name='_rgd_imagery_processedimage_ancillary_files_+',
                        to='rgd.ChecksumFile',
                    ),
                ),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
            bases=(models.Model, rgd.models.mixins.PermissionPathMixin),
        ),
        migrations.CreateModel(
            name='ProcessedImageGroup',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
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
                    'process_type',
                    models.CharField(
                        choices=[
                            ('arbitrary', 'Arbitrarily processed externally'),
                            ('cog', 'Converted to Cloud Optimized GeoTIFF'),
                            ('region', 'Extract subregion'),
                            ('resample', 'Resample by factor'),
                            ('mosaic', 'Mosaic multiple images'),
                        ],
                        default='arbitrary',
                        max_length=20,
                    ),
                ),
                ('parameters', models.JSONField(blank=True, null=True)),
            ],
            options={
                'get_latest_by': 'modified',
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='regionimage',
            name='processed_image',
        ),
        migrations.RemoveField(
            model_name='regionimage',
            name='source_image',
        ),
        migrations.AlterField(
            model_name='raster',
            name='ancillary_files',
            field=models.ManyToManyField(
                blank=True,
                related_name='_rgd_imagery_raster_ancillary_files_+',
                to='rgd.ChecksumFile',
            ),
        ),
        migrations.DeleteModel(
            name='ConvertedImage',
        ),
        migrations.DeleteModel(
            name='RegionImage',
        ),
        migrations.AddField(
            model_name='processedimage',
            name='group',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to='rgd_imagery.processedimagegroup'
            ),
        ),
        migrations.AddField(
            model_name='processedimage',
            name='processed_image',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to='rgd_imagery.image',
            ),
        ),
        migrations.AddField(
            model_name='processedimage',
            name='source_images',
            field=models.ManyToManyField(to='rgd_imagery.Image'),
        ),
    ]
