import logging

from rest_framework import serializers
from rgd.permissions import check_write_perm
from rgd.serializers import ChecksumFileSerializer

from .. import models
from .base import ImageSerializer

logger = logging.getLogger(__name__)


class ProcessedImageGroupSerializer(serializers.ModelSerializer):
    def validate_source_image(self, value):
        if 'request' in self.context:
            check_write_perm(self.context['request'].user, value)
        return value

    class Meta:
        model = models.ProcessedImageGroup
        fields = '__all__'
        read_only_fields = [
            'id',
            'modified',
            'created',
        ]


class ProcessedImageSerializer(serializers.ModelSerializer):

    # group = ProcessedImageGroupSerializer()
    # source_images = ImageSerializer(many=True, required=False)
    processed_image = ImageSerializer(required=False)
    ancillary_files = ChecksumFileSerializer(many=True, required=False)

    def validate_source_image(self, value):
        if 'request' in self.context:
            check_write_perm(self.context['request'].user, value)
        return value

    class Meta:
        model = models.ProcessedImage
        fields = '__all__'
        read_only_fields = [
            'id',
            'status',
            'failure_reason',
            'modified',
            'created',
        ]

    # def create(self, validated_data):
    #     """Prevent duplicated subsamples from being created."""
    #     source_images = validated_data.pop('source_images')
    #     obj, created = models.ProcessedImage.objects.get_or_create(**validated_data)
    #     obj.source_images.add(*source_images)
    #     if not created:
    #         # Trigger save event to reprocess the subsampling
    #         obj.save()
    #     return obj
