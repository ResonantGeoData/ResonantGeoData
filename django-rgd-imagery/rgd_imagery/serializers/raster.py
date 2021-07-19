from rest_framework import serializers
from rgd.serializers import ChecksumFileSerializer, SpatialEntrySerializer

from .. import models
from .base import ImageSetSerializer


class RasterSerializer(serializers.ModelSerializer):
    image_set = ImageSetSerializer()
    ancillary_files = ChecksumFileSerializer(many=True)

    class Meta:
        model = models.Raster
        fields = '__all__'


class RasterMetaSerializer(SpatialEntrySerializer):
    parent_raster = RasterSerializer()

    class Meta:
        model = models.RasterMeta
        exclude = ['footprint', 'outline']
