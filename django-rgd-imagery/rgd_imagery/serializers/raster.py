from rest_framework import serializers
from rgd.models import ChecksumFile
from rgd.serializers import ChecksumFileSerializer, SpatialEntrySerializer

from .. import models
from .base import ImageSetSerializer


class RasterSerializer(serializers.ModelSerializer):
    image_set = ImageSetSerializer(read_only=True)
    image_set_id = serializers.PrimaryKeyRelatedField(
        queryset=models.ImageSet.objects.all(), write_only=True
    )
    ancillary_files = ChecksumFileSerializer(many=True, read_only=True)
    ancillary_files_ids = serializers.PrimaryKeyRelatedField(
        queryset=ChecksumFile.objects.all(), write_only=True, many=True
    )

    class Meta:
        model = models.Raster
        fields = '__all__'


class RasterMetaSerializer(SpatialEntrySerializer):
    """This is read-only."""

    parent_raster = RasterSerializer(read_only=True)

    class Meta:
        model = models.RasterMeta
        exclude = ['footprint', 'outline']
