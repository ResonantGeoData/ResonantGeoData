import json

from rest_framework import serializers

from . import models, utility


class ChecksumFileSerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['download_url'] = value.get_url()
        return ret

    class Meta:
        model = models.ChecksumFile
        fields = '__all__'
        read_only_fields = ['id', 'checksum', 'last_validation', 'modified', 'created']


class SpatialEntrySerializer(serializers.ModelSerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        # NOTE: including footprint can cause the search results to blow up in size
        ret['outline'] = json.loads(value.outline.geojson)
        # NOTE HACK: this is dirty but it works
        subentry = models.SpatialEntry.objects.filter(pk=value.pk).select_subclasses().first()
        # Add hyperlink to get view for subtype if SpatialEntry
        ret['subentry_type'] = type(subentry).__name__
        try:
            # TODO: enforce all sub models have name
            ret['subentry_name'] = subentry.name
        except AttributeError:
            pass
        return ret

    class Meta:
        model = models.SpatialEntry
        exclude = ['footprint', 'outline']


class SpatialEntryFootprintSerializer(SpatialEntrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['footprint'] = json.loads(value.footprint.geojson)
        return ret

    class Meta:
        model = models.SpatialEntry
        exclude = ['footprint', 'outline']


utility.make_serializers(globals(), models)
