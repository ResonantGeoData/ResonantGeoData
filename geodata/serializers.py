from rest_framework import serializers

from .models import GeometryEntry, RasterEntry, SpatialEntry


class GeometryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = GeometryEntry
        fields = '__all__'


class RasterEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = RasterEntry
        fields = '__all__'


class SpatialEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = SpatialEntry
        fields = '__all__'
