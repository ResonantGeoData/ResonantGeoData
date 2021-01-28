import json

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.reverse import reverse

from rgd import utility

from . import models


def _build_related_url(context, relative_uri):
    if 'request' in context:
        request = context['request']
        relative_uri = request.build_absolute_uri(relative_uri)
    return relative_uri


class SpatialEntrySerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['footprint'] = json.loads(value.footprint.geojson)
        ret['outline'] = json.loads(value.outline.geojson)
        return ret

    class Meta:
        model = models.SpatialEntry
        fields = '__all__'


class GeometryEntrySerializer(SpatialEntrySerializer):
    class Meta:
        model = models.GeometryEntry
        exclude = ['data']


class ConvertedImageFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ConvertedImageFile
        fields = ['source_image', 'pk', 'status', 'failure_reason']
        read_only_fields = ['pk', 'status', 'failure_reason']


class ChecksumFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ChecksumFile
        fields = [
            'pk',
            'type',
            'file',
            'url',
            'validate_checksum',
            'name',
            'checksum',
            'last_validation',
            'modified',
            'created',
        ]
        read_only_fields = ['pk', 'checksum', 'last_validation', 'modified', 'created']


class SubsampledImageSerializer(serializers.ModelSerializer):

    data = serializers.HyperlinkedRelatedField(
        many=False, read_only=True, view_name='checksum-file-data'
    )

    def to_representation(self, value):
        ret = super().to_representation(value)
        relative_status_uri = reverse('subsampled-status', args=[value.id])
        ret['status'] = _build_related_url(self.context, relative_status_uri)
        return ret

    class Meta:
        model = models.SubsampledImage
        fields = [
            'source_image',
            'sample_type',
            'sample_parameters',
            'pk',
            'status',
            'failure_reason',
            'modified',
            'created',
            'data',
        ]
        read_only_fields = [
            'pk',
            'status',
            'failure_reason',
            'modified',
            'created',
            'data',
        ]

    def create(self, validated_data):
        """Prevent duplicated subsamples from being created."""
        obj, created = models.SubsampledImage.objects.get_or_create(**validated_data)
        if not created:
            # Trigger save event to reprocess the subsampling
            obj.save()
        return obj


class ImageEntrySerializer(serializers.ModelSerializer):
    annotation_set = serializers.PrimaryKeyRelatedField(
        many=True, queryset=models.Annotation.objects.all(), allow_null=True
    )

    def to_representation(self, value):
        ret = super().to_representation(value)
        relative_data_uri = reverse('image-entry-data', args=[value.id])
        ret['data'] = _build_related_url(self.context, relative_data_uri)
        return ret

    class Meta:
        model = models.ImageEntry
        fields = [
            'pk',
            'modified',
            'created',
            'name',
            'description',
            'instrumentation',
            'image_file',
            'driver',
            'height',
            'width',
            'number_of_bands',
            'metadata',
            'annotation_set',
        ]
        read_only_fields = [
            'pk',
            'modified',
            'created',
            'image_file',
            'driver',
            'height',
            'width',
            'number_of_bands',
            'metadata',
            'annotation_set',
        ]


class PolygonSegmentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.PolygonSegmentation
        fields = [
            'pk',
            'annotation',
            'outline',
            'feature',
        ]
        read_only_fields = [
            'pk',
        ]


class RLESegmentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RLESegmentation
        fields = [
            'pk',
            'annotation',
            'outline',
            'blob',
            'height',
            'width',
        ]
        read_only_fields = [
            'pk',
        ]


class AnnotationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Annotation
        fields = [
            'pk',
            'modified',
            'created',
            'image',
            'caption',
            'label',
            'annotator',
            'notes',
            'keypoints',
            'line',
        ]
        read_only_fields = ['pk', 'modified', 'created']


class KWCOCOArchiveSerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        relative_status_uri = reverse('get-status', args=['KWCOCOArchive', value.id])
        ret['status'] = _build_related_url(self.context, relative_status_uri)
        # Now add images
        try:
            ret['count'] = value.image_set.count
            ret['images'] = [im.pk for im in value.image_set.images.all()]
        except ObjectDoesNotExist:
            pass
        return ret

    class Meta:
        model = models.KWCOCOArchive
        fields = [
            'pk',
            'modified',
            'created',
            'name',
            'failure_reason',
            'status',
            'spec_file',
            'image_archive',
            'image_set',
        ]
        read_only_fields = [
            'pk',
            'modified',
            'created',
            'image_set',
            'failure_reason',
            'status',
        ]


utility.make_serializers(globals(), models)
