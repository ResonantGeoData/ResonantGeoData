from rest_framework import serializers

from .models.raster.base import RasterEntry


class RasterEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = RasterEntry
        fields = '__all__'
