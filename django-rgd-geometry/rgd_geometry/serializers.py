import json

from rgd.models.file import ChecksumFile
from rgd.serializers import (
    TASK_EVENT_READ_ONLY_FIELDS,
    ChecksumFileSerializer,
    RelatedField,
    SpatialEntrySerializer,
)

from . import models


class GeometryArchiveSerializer(SpatialEntrySerializer):
    file = RelatedField(queryset=ChecksumFile.objects.all(), serializer=ChecksumFileSerializer)

    class Meta:
        model = models.GeometryArchive
        fields = '__all__'
        read_only_fields = TASK_EVENT_READ_ONLY_FIELDS


class GeometrySerializer(SpatialEntrySerializer):
    class Meta:
        model = models.Geometry
        exclude = ['data', 'footprint']


class GeometryDataSerializer(GeometrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['data'] = json.loads(value.data.geojson)
        return ret

    class Meta:
        model = models.Geometry
        fields = '__all__'
