import json

from rest_framework import serializers

from .models import GeometryEntry, RasterEntry, SpatialEntry


class SpatialEntrySerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['footprint'] = json.loads(value.footprint.geojson)
        return ret

    class Meta:
        model = SpatialEntry
        fields = '__all__'


class GeometryEntrySerializer(SpatialEntrySerializer):
    class Meta:
        model = GeometryEntry
        exclude = ['data']


class RasterEntrySerializer(SpatialEntrySerializer):
    class Meta:
        model = RasterEntry
        fields = '__all__'
