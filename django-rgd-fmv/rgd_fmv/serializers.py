import json

from rest_framework import serializers
from rgd import utility
from rgd.serializers import ChecksumFileSerializer, SpatialEntrySerializer

from . import models


class FMVSerializer(serializers.ModelSerializer):
    file = ChecksumFileSerializer()

    class Meta:
        model = models.FMV
        fields = '__all__'


class FMVMetaSerializer(SpatialEntrySerializer):
    fmv_file = FMVSerializer()

    class Meta:
        model = models.FMVMeta
        exclude = [
            'ground_frames',
            'ground_union',
            'flight_path',
            'frame_numbers',
            'outline',
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


utility.make_serializers(globals(), models)
