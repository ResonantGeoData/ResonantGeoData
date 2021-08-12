from rest_framework import serializers
from rgd.permissions import check_write_perm
from rgd.serializers import ChecksumFileSerializer

from .. import models
from .base import ImageSerializer


class ProcessedImageSerializer(serializers.ModelSerializer):

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
        ]

    def create(self, validated_data):
        """Prevent duplicated subsamples from being created."""
        obj, created = models.ProcessedImage.objects.get_or_create(**validated_data)
        if not created:
            # Trigger save event to reprocess the subsampling
            obj.save()
        return obj
