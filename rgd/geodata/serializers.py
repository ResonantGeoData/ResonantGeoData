import json

from rest_framework import serializers
from rest_framework.reverse import reverse

from rgd import utility

from . import models


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


class ArbitraryFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ArbitraryFile
        fields = [
            'pk',
            'file',
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
        many=False, read_only=True, view_name='arbitrary-file-data'
    )

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

    def create(self, validated_data):
        """Prevent duplicated subsamples from being created.

        This will check to see if an existing model matches the
        ``sample_parameters`` for the given image ID and return that object
        instead of creating another.

        """
        sample_parameters = validated_data['sample_parameters']
        source_image = validated_data['source_image']
        q = models.SubsampledImage.objects.filter(
            sample_parameters=sample_parameters, source_image=source_image
        )
        if q.count() == 0:
            obj = models.SubsampledImage.objects.create(**validated_data)
        else:
            obj = q.first()
        return obj


utility.make_serializers(globals(), models)
