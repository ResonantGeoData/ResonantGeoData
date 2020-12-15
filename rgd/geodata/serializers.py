import json

from rest_framework import serializers

from rgd import utility

from . import models


class SpatialEntrySerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['footprint'] = json.loads(value.footprint.geojson)
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


class ArbitraryFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ArbitraryFile
        fields = [
            'file',
            'validate_checksum',
            'name',
            'checksum',
            'last_validation',
            'modified',
            'created',
        ]
        read_only_fields = ['checksum', 'last_validation', 'modified', 'created']


class SubsampledImageSerializer(serializers.ModelSerializer):

    data = serializers.HyperlinkedRelatedField(
        many=False, read_only=True, view_name='arbitrary-file'
    )

    class Meta:
        model = models.SubsampledImage
        fields = [
            'source_image',
            'sample_type',
            'sample_parameters',
            'pk',
            'status',
            'failure_reason',
            'data',
        ]
        read_only_fields = [
            'pk',
            'status',
            'failure_reason',
            'data',
        ]


utility.make_serializers(globals(), models)
