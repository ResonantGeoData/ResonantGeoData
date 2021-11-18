from rest_framework import serializers
from rest_framework.reverse import reverse
from rgd.models import ChecksumFile
from rgd.serializers import (
    MODIFIABLE_READ_ONLY_FIELDS,
    TASK_EVENT_READ_ONLY_FIELDS,
    ChecksumFileSerializer,
    RelatedField,
    SpatialEntrySerializer,
)

from .. import models


class ImageSerializer(serializers.ModelSerializer):
    file = RelatedField(queryset=ChecksumFile.objects.all(), serializer=ChecksumFileSerializer)

    class Meta:
        model = models.Image
        fields = '__all__'
        read_only_fields = MODIFIABLE_READ_ONLY_FIELDS + TASK_EVENT_READ_ONLY_FIELDS


class ImageMetaSerializer(serializers.ModelSerializer):
    """This is read-only."""

    parent_image = ImageSerializer(read_only=True)

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
        model = models.ImageMeta
        fields = '__all__'
        # read_only_fields - This serializer should be used read-only


class ImageSetSerializer(serializers.ModelSerializer):
    images = RelatedField(
        queryset=models.Image.objects.all(), serializer=ImageSerializer, many=True
    )

    class Meta:
        model = models.ImageSet
        fields = '__all__'
        read_only_fields = MODIFIABLE_READ_ONLY_FIELDS

    def to_representation(self, value):
        ret = super().to_representation(value)
        # Add processed images
        ret['processed_images'] = [ImageSerializer(im).data for im in value.processed_images.all()]
        return ret


class ImageSetSpatialSerializer(SpatialEntrySerializer):
    image_set = RelatedField(queryset=models.ImageSet.objects.all(), serializer=ImageSetSerializer)

    class Meta:
        model = models.ImageSetSpatial
        fields = '__all__'
        read_only_fields = MODIFIABLE_READ_ONLY_FIELDS
