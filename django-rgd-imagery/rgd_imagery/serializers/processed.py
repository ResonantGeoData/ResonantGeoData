from rest_framework import serializers
from rgd.models import ChecksumFile
from rgd.permissions import check_write_perm
from rgd.serializers import (
    MODIFIABLE_READ_ONLY_FIELDS,
    TASK_EVENT_READ_ONLY_FIELDS,
    ChecksumFileSerializer,
    RelatedField,
)

from .. import models
from .base import ImageSerializer


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

    group = RelatedField(
        queryset=models.ProcessedImageGroup.objects.all(), serializer=ProcessedImageGroupSerializer
    )
    source_images = RelatedField(
        queryset=models.Image.objects.all(), serializer=ImageSerializer, many=True
    )
    processed_image = RelatedField(
        queryset=models.Image.objects.all(), serializer=ImageSerializer, required=False
    )
    ancillary_files = RelatedField(
        queryset=ChecksumFile.objects.all(),
        serializer=ChecksumFileSerializer,
        many=True,
        required=False,
    )

    def validate_source_image(self, value):
        if 'request' in self.context:
            check_write_perm(self.context['request'].user, value)
        return value

    class Meta:
        model = models.ProcessedImage
        fields = '__all__'
        read_only_fields = MODIFIABLE_READ_ONLY_FIELDS + TASK_EVENT_READ_ONLY_FIELDS

    # def create(self, validated_data):
    #     """Prevent duplicated subsamples from being created."""
    #     source_images = validated_data.pop('source_images')
    #     obj, created = models.ProcessedImage.objects.get_or_create(**validated_data)
    #     obj.source_images.add(*source_images)
    #     if not created:
    #         # Trigger save event to reprocess the subsampling
    #         obj.save()
    #     return obj
