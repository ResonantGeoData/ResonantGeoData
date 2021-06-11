import json

from rest_framework import serializers
from rgd import utility
from rgd.serializers import ChecksumFileSerializer, SpatialEntrySerializer

from . import models


class FMVFileSerializer(serializers.ModelSerializer):
    file = ChecksumFileSerializer()

    class Meta:
        model = models.FMVFile
        fields = '__all__'


class FMVEntrySerializer(SpatialEntrySerializer):
    fmv_file = FMVFileSerializer()

    class Meta:
        model = models.FMVEntry
        exclude = [
            'ground_frames',
            'ground_union',
            'flight_path',
            'frame_numbers',
            'outline',
            'footprint',
        ]


class FMVEntryDataSerializer(FMVEntrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['ground_frames'] = json.loads(value.ground_frames.geojson)
        ret['ground_union'] = json.loads(value.ground_union.geojson)
        ret['flight_path'] = json.loads(value.flight_path.geojson)
        return ret

    class Meta:
        model = models.FMVEntry
        fields = '__all__'


utility.make_serializers(globals(), models)
