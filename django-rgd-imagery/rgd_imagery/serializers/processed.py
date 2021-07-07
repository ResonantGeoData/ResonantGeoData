from rest_framework import serializers
from rest_framework.reverse import reverse
from rgd.permissions import check_write_perm

from .. import models
from .base import ImageSerializer


class ConvertedImageSerializer(serializers.ModelSerializer):

    processed_image = ImageSerializer(read_only=True)

    def validate_source_image(self, value):
        if 'request' in self.context:
            check_write_perm(self.context['request'].user, value)
        return value

    class Meta:
        model = models.ConvertedImage
        fields = '__all__'
        read_only_fields = ['id', 'status', 'failure_reason', 'processed_image']


class RegionImageSerializer(serializers.ModelSerializer):

    processed_image = ImageSerializer(read_only=True)

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
        model = models.RegionImage
        fields = '__all__'
        read_only_fields = [
            'id',
            'status',
            'failure_reason',
            'processed_image',
        ]

    def create(self, validated_data):
        """Prevent duplicated subsamples from being created."""
        obj, created = models.RegionImage.objects.get_or_create(**validated_data)
        if not created:
            # Trigger save event to reprocess the subsampling
            obj.save()
        return obj
