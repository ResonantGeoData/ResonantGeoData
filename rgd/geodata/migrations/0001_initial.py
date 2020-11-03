# Generated by Django 3.1.2 on 2020-11-03 17:08

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion
import s3_file_field.fields

import rgd.geodata.models.geometry.base
import rgd.geodata.models.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='BaseImageFile',
            fields=[
                ('image_file_id', models.AutoField(primary_key=True, serialize=False)),
            ],
        ),
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
            name='Segmentation',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                (
                    'outline',
                    django.contrib.gis.db.models.fields.PolygonField(
                        help_text='The bounding box', null=True, srid=0
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
                    django.contrib.gis.db.models.fields.PolygonField(blank=True, srid=4326),
                ),
                (
                    'outline',
                    django.contrib.gis.db.models.fields.PolygonField(blank=True, srid=4326),
                ),
            ],
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
                ('annotator', models.CharField(blank=True, max_length=100, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                (
                    'keypoints',
                    django.contrib.gis.db.models.fields.MultiPointField(null=True, srid=0),
                ),
                ('line', django.contrib.gis.db.models.fields.LineStringField(null=True, srid=0)),
            ],
            bases=('geodata.modifiableentry',),
        ),
        migrations.CreateModel(
            name='ArbitraryFile',
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
                ('name', models.CharField(blank=True, max_length=100)),
                ('checksum', models.CharField(max_length=64)),
                ('validate_checksum', models.BooleanField(default=False)),
                ('last_validation', models.BooleanField(default=True)),
                (
                    'file',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
            bases=('geodata.modifiableentry',),
        ),
        migrations.CreateModel(
            name='FMVFile',
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
                ('name', models.CharField(blank=True, max_length=100)),
                ('checksum', models.CharField(max_length=64)),
                ('validate_checksum', models.BooleanField(default=False)),
                ('last_validation', models.BooleanField(default=True)),
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
                    'file',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                    ),
                ),
                (
                    'klv_file',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        null=True,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                    ),
                ),
                (
                    'web_video_file',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        null=True,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                    ),
                ),
                ('frame_rate', models.FloatField(null=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('geodata.modifiableentry', rgd.geodata.models.mixins.TaskEventMixin),
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
                ('name', models.CharField(blank=True, max_length=100)),
                ('checksum', models.CharField(max_length=64)),
                ('validate_checksum', models.BooleanField(default=False)),
                ('last_validation', models.BooleanField(default=True)),
                (
                    'file',
                    s3_file_field.fields.S3FileField(
                        help_text='This must be an archive (`.zip` or `.tar`) of a single shape (`.shp`, `.dbf`, `.shx`, etc.).',
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                        validators=[rgd.geodata.models.geometry.base.validate_archive],
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
            ],
            options={
                'abstract': False,
            },
            bases=('geodata.modifiableentry', rgd.geodata.models.mixins.TaskEventMixin),
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
                ('name', models.CharField(blank=True, max_length=100)),
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
                ('metadata', models.JSONField(null=True)),
                (
                    'image_file',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.baseimagefile'
                    ),
                ),
            ],
            bases=('geodata.modifiableentry',),
        ),
        migrations.CreateModel(
            name='ImageFile',
            fields=[
                (
                    'baseimagefile_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        to='geodata.baseimagefile',
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
                ('name', models.CharField(blank=True, max_length=100)),
                ('checksum', models.CharField(max_length=64)),
                ('validate_checksum', models.BooleanField(default=False)),
                ('last_validation', models.BooleanField(default=True)),
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
                    'file',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
            bases=(
                'geodata.modifiableentry',
                rgd.geodata.models.mixins.TaskEventMixin,
                'geodata.baseimagefile',
            ),
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
                ('name', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('images', models.ManyToManyField(to='geodata.ImageEntry')),
            ],
            bases=('geodata.modifiableentry',),
        ),
        migrations.CreateModel(
            name='PolygonSegmentation',
            fields=[
                (
                    'segmentation_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.segmentation',
                    ),
                ),
                (
                    'feature',
                    django.contrib.gis.db.models.fields.MultiPolygonField(null=True, srid=0),
                ),
            ],
            bases=('geodata.segmentation',),
        ),
        migrations.CreateModel(
            name='RasterEntry',
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
                ('name', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
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
                    'image_set',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.imageset'
                    ),
                ),
            ],
            bases=('geodata.modifiableentry', rgd.geodata.models.mixins.TaskEventMixin),
        ),
        migrations.CreateModel(
            name='RLESegmentation',
            fields=[
                (
                    'segmentation_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.segmentation',
                    ),
                ),
                ('blob', models.BinaryField()),
                ('height', models.PositiveIntegerField()),
                ('width', models.PositiveIntegerField()),
            ],
            bases=('geodata.segmentation',),
        ),
        migrations.CreateModel(
            name='Thumbnail',
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
                ('base_thumbnail', models.ImageField(upload_to='thumbnails')),
                (
                    'image_entry',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.imageentry'
                    ),
                ),
            ],
            bases=('geodata.modifiableentry',),
        ),
        migrations.AddField(
            model_name='segmentation',
            name='annotation',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, to='geodata.annotation'
            ),
        ),
        migrations.CreateModel(
            name='RasterMetaEntry',
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
                ('crs', models.TextField(help_text='PROJ string')),
                (
                    'origin',
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.FloatField(), size=2
                    ),
                ),
                (
                    'extent',
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.FloatField(), size=4
                    ),
                ),
                (
                    'resolution',
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.FloatField(), size=2
                    ),
                ),
                (
                    'transform',
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.FloatField(), size=6
                    ),
                ),
                (
                    'parent_raster',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.rasterentry'
                    ),
                ),
            ],
            bases=('geodata.modifiableentry', 'geodata.spatialentry'),
        ),
        migrations.CreateModel(
            name='KWCOCOArchive',
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
                ('name', models.CharField(blank=True, max_length=100)),
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
                    'image_archive',
                    models.OneToOneField(
                        help_text='An archive (.tar or .zip) of the images referenced by the spec file (optional).',
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='kwcoco_image_archive',
                        to='geodata.arbitraryfile',
                    ),
                ),
                (
                    'image_set',
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to='geodata.imageset',
                    ),
                ),
                (
                    'spec_file',
                    models.OneToOneField(
                        help_text='The JSON spec file.',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='kwcoco_spec_file',
                        to='geodata.arbitraryfile',
                    ),
                ),
            ],
            bases=('geodata.modifiableentry', rgd.geodata.models.mixins.TaskEventMixin),
        ),
        migrations.CreateModel(
            name='ImageArchiveFile',
            fields=[
                (
                    'baseimagefile_ptr',
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to='geodata.baseimagefile',
                    ),
                ),
                (
                    'path',
                    models.TextField(
                        help_text='The relative path to the image inside the archive.'
                    ),
                ),
                (
                    'archive',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.arbitraryfile'
                    ),
                ),
            ],
            bases=('geodata.baseimagefile',),
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
                ('name', models.CharField(blank=True, max_length=100)),
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
            name='FMVEntry',
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
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('ground_frames', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
                ('ground_union', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326)),
                ('flight_path', django.contrib.gis.db.models.fields.MultiPointField(srid=4326)),
                ('frame_numbers', models.BinaryField()),
                (
                    'fmv_file',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.fmvfile'
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
                ('name', models.CharField(blank=True, max_length=100)),
                ('checksum', models.CharField(max_length=64)),
                ('validate_checksum', models.BooleanField(default=False)),
                ('last_validation', models.BooleanField(default=True)),
                (
                    'file',
                    s3_file_field.fields.S3FileField(
                        max_length=2000,
                        upload_to=s3_file_field.fields.S3FileField.uuid_prefix_filename,
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
                    'source_image',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.imageentry'
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
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
                ('band_number', models.IntegerField()),
                (
                    'description',
                    models.TextField(
                        blank=True,
                        help_text='Automatically retreived from raster but can be overwritten.',
                        null=True,
                    ),
                ),
                ('dtype', models.CharField(max_length=10)),
                ('max', models.FloatField()),
                ('min', models.FloatField()),
                ('mean', models.FloatField()),
                ('std', models.FloatField()),
                ('nodata_value', models.FloatField(null=True)),
                ('interpretation', models.TextField()),
                (
                    'parent_image',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='geodata.imageentry'
                    ),
                ),
            ],
            bases=('geodata.modifiableentry',),
        ),
        migrations.AddField(
            model_name='annotation',
            name='image',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to='geodata.imageentry'
            ),
        ),
    ]
