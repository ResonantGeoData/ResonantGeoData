import json

from rgd import utility
from rgd.serializers import SpatialEntrySerializer

from . import models


class GeometryEntrySerializer(SpatialEntrySerializer):
    class Meta:
        model = models.GeometryEntry
        exclude = ['data', 'footprint', 'outline']


class GeometryEntryDataSerializer(GeometryEntrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['data'] = json.loads(value.data.geojson)
        return ret

    class Meta:
        model = models.GeometryEntry
        fields = '__all__'


utility.make_serializers(globals(), models)
