import base64
import json

from django.contrib.gis.geos import Polygon
from django.db import transaction
from pyproj import CRS
import pystac
from rest_framework import serializers
from rest_framework.reverse import reverse

from rgd import utility
from rgd.geodata.permissions import check_write_perm

from . import models


class SpatialEntrySerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        # NOTE: including footprint can cause the search results to blow up in size
        ret['outline'] = json.loads(value.outline.geojson)
        # Add hyperlink to get view for subtype if SpatialEntry
        if type(value).__name__ != value.subentry_type:
            subtype = value.subentry_type
            ret['subentry_type'] = subtype
            ret['subentry_pk'] = value.subentry.pk
            ret['subentry_name'] = value.subentry_name
            if subtype == 'RasterMetaEntry':
                ret['subentry_pk'] = value.subentry.pk
                subtype_uri = reverse('raster-meta-entry', args=[value.subentry.pk])
            elif subtype == 'GeometryEntry':
                subtype_uri = reverse('geometry-entry', args=[value.subentry.pk])
            elif subtype == 'FMVEntry':
                subtype_uri = reverse('fmv-entry', args=[value.subentry.pk])
            if 'request' in self.context:
                request = self.context['request']
                ret['detail'] = request.build_absolute_uri(subtype_uri)
            else:
                ret['detail'] = subtype_uri
        return ret

    class Meta:
        model = models.SpatialEntry
        exclude = ['footprint', 'outline']


class SpatialEntryFootprintSerializer(SpatialEntrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['footprint'] = json.loads(value.footprint.geojson)
        return ret

    class Meta:
        model = models.SpatialEntry
        exclude = ['footprint', 'outline']


class GeometryEntrySerializer(SpatialEntrySerializer):
    class Meta:
        model = models.GeometryEntry
        exclude = ['data', 'footprint', 'outline']


class GeometryEntryDataSerializer(GeometryEntrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['data'] = json.loads(value.data.geojson)
        return ret

    class Meta:
        model = models.GeometryEntry
        fields = '__all__'


class ConvertedImageFileSerializer(serializers.ModelSerializer):
    def validate_source_image(self, value):
        if 'request' in self.context:
            check_write_perm(self.context['request'].user, value)
        return value

    class Meta:
        model = models.ConvertedImageFile
        fields = '__all__'
        read_only_fields = ['id', 'status', 'failure_reason', 'converted_file']


class ChecksumFileSerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['download_url'] = value.get_url()
        return ret

    class Meta:
        model = models.ChecksumFile
        fields = '__all__'
        read_only_fields = ['id', 'checksum', 'last_validation', 'modified', 'created']


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


class FMVFileSerializer(serializers.ModelSerializer):
    file = ChecksumFileSerializer()

    class Meta:
        model = models.FMVFile
        fields = '__all__'


class FMVEntrySerializer(SpatialEntrySerializer):
    fmv_file = FMVFileSerializer()

    class Meta:
        model = models.FMVEntry
        exclude = [
            'ground_frames',
            'ground_union',
            'flight_path',
            'frame_numbers',
            'outline',
            'footprint',
        ]


class FMVEntryDataSerializer(FMVEntrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['ground_frames'] = json.loads(value.ground_frames.geojson)
        ret['ground_union'] = json.loads(value.ground_union.geojson)
        ret['flight_path'] = json.loads(value.flight_path.geojson)
        return ret

    class Meta:
        model = models.FMVEntry
        fields = '__all__'


class STACRasterSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        item = pystac.Item.from_dict(data)
        errors = item.validate()
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def to_representation(self, instance: models.RasterMetaEntry) -> dict:
        item = pystac.Item(
            id=instance.pk,
            geometry=json.loads(instance.footprint.json),
            bbox=instance.extent,
            datetime=(instance.acquisition_date or instance.modified or instance.created),
            properties={},
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
        for name in item.assets:
            asset = item.assets[name]
            checksum_file, _ = models.ChecksumFile.objects.get_or_create(
                type=models.FileSourceType.URL,
                url=asset.href,
            )
            if 'data' in asset.roles:
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
        )
        instance.save()
        return instance


class PointCloudFileSerializer(serializers.ModelSerializer):
    file = ChecksumFileSerializer()

    class Meta:
        model = models.PointCloudFile
        fields = '__all__'


class PointCloudEntrySerializer(serializers.ModelSerializer):
    source = PointCloudFileSerializer()
    vtp_data = ChecksumFileSerializer()

    def to_representation(self, value):
        ret = super().to_representation(value)
        return ret

    class Meta:
        model = models.PointCloudEntry
        fields = '__all__'


class PointCloudEntryDataSerializer(PointCloudEntrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        # Extract data as base64
        with value.vtp_data.yield_local_path() as path:
            with open(path, 'rb') as data:
                data_content = data.read()
                base64_content = base64.b64encode(data_content)
                base64_content = base64_content.decode().replace('\n', '')
        ret['vtp_data'] = base64_content
        return ret


utility.make_serializers(globals(), models)
