from rest_framework import serializers
from rest_framework.reverse import reverse
from rgd.serializers import ChecksumFileSerializer

from .. import models


class ImageSerializer(serializers.ModelSerializer):
    file = ChecksumFileSerializer()

    class Meta:
        model = models.Image
        fields = '__all__'


class ImageMetaSerializer(serializers.ModelSerializer):
    parent_image = ImageSerializer()

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
    images = ImageSerializer(many=True)

    class Meta:
        model = models.ImageSet
        fields = '__all__'
        read_only_fields = [
            'id',
            'modified',
            'created',
        ]
