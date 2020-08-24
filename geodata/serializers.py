import json

from rest_framework import serializers

from rgd import utility
from . import models


class GeometryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.GeometryEntry
        fields = '__all__'
        read_only_fields = ['geometry_archive', 'spatialentry_ptr']


class RasterEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.RasterEntry
        fields = '__all__'
        read_only_fields = ['spatialentry_ptr']


class SpatialEntrySerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['footprint'] = json.loads(value.footprint.geojson)
        return ret

    class Meta:
        model = models.SpatialEntry
        fields = '__all__'


utility.make_serializers(globals(), models)
