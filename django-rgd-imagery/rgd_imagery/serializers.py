import json

import dateutil.parser
from django.contrib.gis.geos import Polygon
from django.db import transaction
from pyproj import CRS
import pystac
from rest_framework import serializers
from rest_framework.reverse import reverse

from rgd import utility
from rgd.permissions import check_write_perm
from rgd.serializers import ChecksumFileSerializer, SpatialEntrySerializer

from . import models


class ConvertedImageFileSerializer(serializers.ModelSerializer):
    def validate_source_image(self, value):
        if 'request' in self.context:
            check_write_perm(self.context['request'].user, value)
        return value

    class Meta:
        model = models.ConvertedImageFile
        fields = '__all__'
        read_only_fields = ['id', 'status', 'failure_reason', 'converted_file']


class SubsampledImageSerializer(serializers.ModelSerializer):

    data = ChecksumFileSerializer(read_only=True)

    def validate_source_image(self, value):
        if 'request' in self.context:
            check_write_perm(self.context['request'].user, value)
        return value

    def to_representation(self, value):
        ret = super().to_representation(value)
        realtive_status_uri = reverse('subsampled-status', args=[value.id])
        if 'request' in self.context:
            request = self.context['request']
            ret['status'] = request.build_absolute_uri(realtive_status_uri)
        else:
            ret['status'] = realtive_status_uri
        return ret

    class Meta:
        model = models.SubsampledImage
        fields = '__all__'
        read_only_fields = [
            'id',
            'status',
            'failure_reason',
            'data',
        ]

    def create(self, validated_data):
        """Prevent duplicated subsamples from being created."""
        obj, created = models.SubsampledImage.objects.get_or_create(**validated_data)
        if not created:
            # Trigger save event to reprocess the subsampling
            obj.save()
        return obj


class ImageFileSerializer(serializers.ModelSerializer):
    file = ChecksumFileSerializer()

    class Meta:
        model = models.ImageFile
        fields = '__all__'


class ImageEntrySerializer(serializers.ModelSerializer):
    image_file = ImageFileSerializer()

    def to_representation(self, value):
        ret = super().to_representation(value)
        realtive_thumbnail_uri = reverse('image-thumbnail', args=[value.id])
        if 'request' in self.context:
            request = self.context['request']
            ret['thumbnail'] = request.build_absolute_uri(realtive_thumbnail_uri)
        else:
            ret['thumbnail'] = realtive_thumbnail_uri
        return ret

    class Meta:
        model = models.ImageEntry
        fields = '__all__'
        read_only_fields = [
            'id',
            'modified',
            'created',
            'driver',
            'height',
            'width',
            'number_of_bands',
        ]


class ImageSetSerializer(serializers.ModelSerializer):
    images = ImageEntrySerializer(many=True)

    class Meta:
        model = models.ImageSet
        fields = '__all__'
        read_only_fields = [
            'id',
            'modified',
            'created',
        ]


class RasterEntrySerializer(serializers.ModelSerializer):
    image_set = ImageSetSerializer()
    ancillary_files = ChecksumFileSerializer(many=True)

    class Meta:
        model = models.RasterEntry
        fields = '__all__'


class RasterMetaEntrySerializer(SpatialEntrySerializer):
    parent_raster = RasterEntrySerializer()

    class Meta:
        model = models.RasterMetaEntry
        exclude = ['footprint', 'outline']


class STACRasterSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        # item = pystac.Item.from_dict(data)
        # errors = item.validate()
        # if errors:
        #     raise serializers.ValidationError(errors)
        return data

    def to_representation(self, instance: models.RasterMetaEntry) -> dict:
        item = pystac.Item(
            id=instance.pk,
            geometry=json.loads(instance.footprint.json),
            bbox=instance.extent,
            datetime=(instance.acquisition_date or instance.modified or instance.created),
            properties=dict(
                datetime=str(instance.acquisition_date),
                platform=instance.instrumentation,
            ),
        )
        # 'proj' extension
        item.ext.enable('projection')
        item.ext.projection.apply(
            epsg=CRS.from_proj4(instance.crs).to_epsg(),
            transform=instance.transform,
        )
        # 'eo' extension
        item.ext.enable('eo')
        item.ext.eo.apply(cloud_cover=instance.cloud_cover, bands=[])
        # Add assets
        for image_entry in instance.parent_raster.image_set.images.all():
            asset = pystac.Asset(
                href=image_entry.image_file.file.get_url(),
                title=image_entry.image_file.file.name,
                roles=[
                    'data',
                ],
            )
            item.ext.eo.set_bands(
                bands=[
                    pystac.extensions.eo.Band.create(
                        name=f'B{bandmeta.band_number}',
                        description=bandmeta.description,
                    )
                    for bandmeta in image_entry.bandmetaentry_set.all()
                ],
                asset=asset,
            )
            item.add_asset(f'image-{image_entry.pk}', asset)

        for ancillary_file in instance.parent_raster.ancillary_files.all():
            asset = pystac.Asset(
                href=ancillary_file.get_url(),
                title=ancillary_file.name,
                roles=[
                    'metadata',
                ],
            )
            item.add_asset(f'ancillary-{ancillary_file.pk}', asset)

        return item.to_dict()

    @transaction.atomic
    def create(self, data):
        # TODO: fix messy import
        from rgd.geodata.models.imagery.etl import read_image_file

        item = pystac.Item.from_dict(data)
        images, ancillary = [], []
        single_asset = False
        if len(item.assets) == 1:
            single_asset = True
        for name in item.assets:
            asset = item.assets[name]
            checksum_file, _ = models.ChecksumFile.objects.get_or_create(
                type=models.FileSourceType.URL,
                url=asset.href,
            )
            if single_asset or (asset.roles and 'data' in asset.roles):
                image_file, _ = utility.get_or_create_no_commit(
                    models.ImageFile, file=checksum_file
                )
                image_file.skip_signal = True
                image_file.save()
                read_image_file(image_file)
                image_entry = models.ImageEntry.objects.get(image_file=image_file)
                images.append(image_entry)
            else:
                ancillary.append(checksum_file)

        image_set = models.ImageSet.objects.create()
        image_set.images.set(images)

        raster_entry = models.RasterEntry()
        raster_entry.skip_signal = True
        raster_entry.name = item.id
        raster_entry.image_set = image_set
        raster_entry.save()
        [raster_entry.ancillary_files.add(af) for af in ancillary]
        raster_entry.save()

        outline = Polygon(
            (
                [item.bbox[0], item.bbox[1]],
                [item.bbox[0], item.bbox[3]],
                [item.bbox[2], item.bbox[3]],
                [item.bbox[2], item.bbox[1]],
                [item.bbox[0], item.bbox[1]],
            )
        )

        instance = models.RasterMetaEntry(
            parent_raster=raster_entry,
            footprint=json.dumps(item.geometry),
            crs=f'+init=epsg:{item.ext.projection.epsg}',
            cloud_cover=item.ext.eo.cloud_cover,
            transform=item.ext.projection.transform,
            extent=item.bbox,
            origin=(item.bbox[0], item.bbox[1]),
            resolution=(0, 0),  # TODO: fix
            outline=outline,
            acquisition_date=dateutil.parser.isoparser().isoparse(item.properties['datetime']),
            instrumentation=item.properties['platform'],
        )
        instance.save()
        return instance


utility.make_serializers(globals(), models)
