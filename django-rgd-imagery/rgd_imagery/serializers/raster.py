from rest_framework import serializers
from rgd.models import ChecksumFile
from rgd.serializers import (
    MODIFIABLE_READ_ONLY_FIELDS,
    TASK_EVENT_READ_ONLY_FIELDS,
    ChecksumFileSerializer,
    RelatedField,
    SpatialEntrySerializer,
)

from .. import models
from .base import ImageSetSerializer


class RasterSerializer(serializers.ModelSerializer):
    image_set = RelatedField(queryset=models.ImageSet.objects.all(), serializer=ImageSetSerializer)
    ancillary_files = RelatedField(
        queryset=ChecksumFile.objects.all(),
        serializer=ChecksumFileSerializer,
        many=True,
        required=False,
    )

    class Meta:
        model = models.Raster
        fields = '__all__'
        read_only_fields = MODIFIABLE_READ_ONLY_FIELDS + TASK_EVENT_READ_ONLY_FIELDS

    def to_representation(self, value):
        ret = super().to_representation(value)
        try:
            ret['raster_meta_id'] = value.rastermeta.pk
        except models.RasterMeta.DoesNotExist:
            ret['raster_meta_id'] = None
        return ret


class RasterMetaSerializer(SpatialEntrySerializer):
    """This is read-only."""

    parent_raster = RasterSerializer(read_only=True)

    class Meta:
        model = models.RasterMeta
        exclude = ['footprint']
        # read_only_fields - This serializer should be used read-only
