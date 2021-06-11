import json

from rest_framework import serializers
from rest_framework.reverse import reverse

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
        # Add hyperlink to get view for subtype if SpatialEntry
        if type(value).__name__ != value.subentry_type:
            subtype = value.subentry_type
            ret['subentry_type'] = subtype
            ret['subentry_pk'] = value.subentry.pk
            ret['subentry_name'] = value.subentry_name
            if subtype == 'RasterMetaEntry':
                ret['subentry_pk'] = value.subentry.pk
                subtype_uri = reverse('raster-meta-entry', args=[value.subentry.pk])
            elif subtype == 'GeometryEntry':
                subtype_uri = reverse('geometry-entry', args=[value.subentry.pk])
            elif subtype == 'FMVEntry':
                subtype_uri = reverse('fmv-entry', args=[value.subentry.pk])
            if 'request' in self.context:
                request = self.context['request']
                ret['detail'] = request.build_absolute_uri(subtype_uri)
            else:
                ret['detail'] = subtype_uri
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
