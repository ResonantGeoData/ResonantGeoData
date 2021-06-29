import json

from rgd import utility
from rgd.serializers import SpatialEntrySerializer

from . import models


class GeometrySerializer(SpatialEntrySerializer):
    class Meta:
        model = models.Geometry
        exclude = ['data', 'footprint', 'outline']


class GeometryDataSerializer(GeometrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['data'] = json.loads(value.data.geojson)
        return ret

    class Meta:
        model = models.Geometry
        fields = '__all__'


utility.make_serializers(globals(), models)
