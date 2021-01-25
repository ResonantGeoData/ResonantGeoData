import json

from rest_framework import serializers
from rest_framework.reverse import reverse

from rgd import utility
from rgd.geodata.permissions import check_write_perm

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
    def validate_source_image(self, value):
        if 'request' in self.context:
            check_write_perm(self.context['request'].user, value)
        return value

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
        """Prevent duplicated subsamples from being created."""
        obj, created = models.SubsampledImage.objects.get_or_create(**validated_data)
        if not created:
            # Trigger save event to reprocess the subsampling
            obj.save()
        return obj


utility.make_serializers(globals(), models)
