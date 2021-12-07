import json

from rest_framework import serializers
from rgd.models.file import ChecksumFile
from rgd.serializers import (
    TASK_EVENT_READ_ONLY_FIELDS,
    ChecksumFileSerializer,
    RelatedField,
    SpatialEntrySerializer,
)

from . import models


class FMVSerializer(serializers.ModelSerializer):
    file = RelatedField(queryset=ChecksumFile.objects.all(), serializer=ChecksumFileSerializer)

    class Meta:
        model = models.FMV
        fields = '__all__'
        read_only_fields = TASK_EVENT_READ_ONLY_FIELDS + ['frame_rate']


class FMVMetaSerializer(SpatialEntrySerializer):
    fmv_file = FMVSerializer()

    class Meta:
        model = models.FMVMeta
        exclude = [
            'ground_frames',
            'ground_union',
            'flight_path',
            'frame_numbers',
            'footprint',
        ]


class FMVMetaDataSerializer(FMVMetaSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['ground_frames'] = json.loads(value.ground_frames.geojson)
        ret['ground_union'] = json.loads(value.ground_union.geojson)
        ret['flight_path'] = json.loads(value.flight_path.geojson)
        return ret

    class Meta:
        model = models.FMVMeta
        fields = '__all__'
