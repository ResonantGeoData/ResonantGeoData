# Generated by Django 3.1rc1 on 2020-07-29 19:37
import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import s3_file_field.fields

import geodata.models.geometry.base
import geodata.models.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ModifiableEntry',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'modified',
                    models.DateTimeField(
                        editable=False, help_text='The last time this entry was saved.'
                    ),
                ),
                (
                    'created',
                    models.DateTimeField(
                        editable=False, help_text='When this was added to the database.'
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='SpatialEntry',
            fields=[
                ('spatial_id', models.AutoField(primary_key=True, serialize=False)),
                ('acquisition_date', models.DateTimeField(blank=True, default=None, null=True)),
                (
                    'footprint',
                    django.contrib.gis.db.models.fields.PolygonField(
                        blank=True, null=True, srid=4326
                    ),
                ),
                (
                    'outline',
                    django.contrib.gis.db.models.fields.PolygonField(
                        blank=True, null=True, srid=4326
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name='GeometryArchive',
            fields=[
                (
                    'modifiableentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.modifiableentry',
                    ),
                ),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('checksum', models.CharField(blank=True, max_length=64, null=True)),
                ('compute_checksum', models.BooleanField(default=False)),
                ('validate_checksum', models.BooleanField(default=False)),
                ('last_validation', models.BooleanField(default=True)),
                (
                    'file',
                    s3_file_field.fields.S3FileField(
                        help_text='This must be an archive (`.zip` or `.tar`) of a single shape (`.shp`, `.dbf`, `.shx`, etc.).',
                        max_length=2000,
                        upload_to='files/geometry_files',
                        validators=[geodata.models.geometry.base.validate_archive],
                    ),
                ),
                ('failure_reason', models.TextField(blank=True, null=True)),
            ],
            options={'abstract': False},
            bases=('geodata.modifiableentry', geodata.models.mixins.TaskEventMixin),
        ),
        migrations.CreateModel(
            name='ImageEntry',
            fields=[
                (
                    'modifiableentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.modifiableentry',
                    ),
                ),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                (
                    'instrumentation',
                    models.CharField(
                        blank=True,
                        help_text='The instrumentation used to acquire these data.',
                        max_length=100,
                        null=True,
                    ),
                ),
                ('driver', models.CharField(max_length=100)),
                ('height', models.PositiveIntegerField()),
                ('width', models.PositiveIntegerField()),
                ('number_of_bands', models.PositiveIntegerField()),
                ('metadata', django.contrib.postgres.fields.jsonb.JSONField(null=True)),
            ],
            bases=('geodata.modifiableentry',),
        ),
        migrations.CreateModel(
            name='ImageFile',
            fields=[
                (
                    'modifiableentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.modifiableentry',
                    ),
                ),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('checksum', models.CharField(blank=True, max_length=64, null=True)),
                ('compute_checksum', models.BooleanField(default=False)),
                ('validate_checksum', models.BooleanField(default=False)),
                ('last_validation', models.BooleanField(default=True)),
                ('failure_reason', models.TextField(blank=True, null=True)),
                (
                    'file',
                    s3_file_field.fields.S3FileField(max_length=2000, upload_to='files/rasters'),
                ),
            ],
            options={'abstract': False},
            bases=('geodata.modifiableentry', geodata.models.mixins.TaskEventMixin),
        ),
        migrations.CreateModel(
            name='ImageSet',
            fields=[
                (
                    'modifiableentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.modifiableentry',
                    ),
                ),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('images', models.ManyToManyField(to='geodata.ImageEntry')),
            ],
            bases=('geodata.modifiableentry',),
        ),
        migrations.CreateModel(
            name='RasterEntry',
            fields=[
                (
                    'spatialentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        to='geodata.spatialentry',
                    ),
                ),
                (
                    'imageset_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.imageset',
                    ),
                ),
                ('crs', models.TextField(help_text='PROJ string', null=True)),
                (
                    'origin',
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.FloatField(), null=True, size=2
                    ),
                ),
                (
                    'extent',
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.FloatField(), null=True, size=4
                    ),
                ),
                (
                    'resolution',
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.FloatField(), null=True, size=2
                    ),
                ),
                (
                    'transform',
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.FloatField(), null=True, size=6
                    ),
                ),
                ('failure_reason', models.TextField(blank=True, null=True)),
            ],
            bases=(
                'geodata.imageset',
                'geodata.spatialentry',
                geodata.models.mixins.TaskEventMixin,
            ),
        ),
        migrations.AddField(
            model_name='imageentry',
            name='image_file',
            field=models.OneToOneField(
                null=True, on_delete=django.db.models.deletion.CASCADE, to='geodata.imagefile'
            ),
        ),
        migrations.CreateModel(
            name='GeometryEntry',
            fields=[
                (
                    'spatialentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        to='geodata.spatialentry',
                    ),
                ),
                (
                    'modifiableentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.modifiableentry',
                    ),
                ),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('data', django.contrib.gis.db.models.fields.GeometryCollectionField(srid=4326)),
                (
                    'geometry_archive',
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='geodata.geometryarchive',
                    ),
                ),
            ],
            bases=('geodata.modifiableentry', 'geodata.spatialentry'),
        ),
        migrations.CreateModel(
            name='ConvertedImageFile',
            fields=[
                (
                    'modifiableentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.modifiableentry',
                    ),
                ),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('checksum', models.CharField(blank=True, max_length=64, null=True)),
                ('compute_checksum', models.BooleanField(default=False)),
                ('validate_checksum', models.BooleanField(default=False)),
                ('last_validation', models.BooleanField(default=True)),
                (
                    'file',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                    ),
                ),
                ('failure_reason', models.TextField(blank=True, null=True)),
                (
                    'source_image',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.imageentry'
                    ),
                ),
            ],
            options={'abstract': False},
            bases=('geodata.modifiableentry',),
        ),
        migrations.CreateModel(
            name='BandMetaEntry',
            fields=[
                (
                    'modifiableentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.modifiableentry',
                    ),
                ),
                (
                    'description',
                    models.TextField(
                        blank=True,
                        help_text='Automatically retreived from raster but can be overwritten.',
                        null=True,
                    ),
                ),
                ('dtype', models.CharField(max_length=10)),
                ('max', models.FloatField(null=True)),
                ('min', models.FloatField(null=True)),
                ('mean', models.FloatField(null=True)),
                ('std', models.FloatField(null=True)),
                ('nodata_value', models.FloatField(null=True)),
                ('interpretation', models.TextField(blank=True, null=True)),
                (
                    'parent_image',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.imageentry'
                    ),
                ),
            ],
            bases=('geodata.modifiableentry',),
        ),
        migrations.CreateModel(
            name='Annotation',
            fields=[
                (
                    'modifiableentry_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.modifiableentry',
                    ),
                ),
                ('caption', models.CharField(blank=True, max_length=100, null=True)),
                ('label', models.CharField(blank=True, max_length=100, null=True)),
                ('bounding_box', django.contrib.gis.db.models.fields.PolygonField(srid=4326)),
                (
                    'feature',
                    django.contrib.gis.db.models.fields.GeometryField(null=True, srid=4326),
                ),
                ('annotator', models.CharField(blank=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                (
                    'image',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.imageentry'
                    ),
                ),
            ],
            bases=('geodata.modifiableentry',),
        ),
    ]
