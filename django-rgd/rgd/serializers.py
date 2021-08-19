import json

from rest_framework import serializers

from . import models, utility


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Collection
        fields = '__all__'


class CollectionPermissionSerializer(serializers.ModelSerializer):
    collection = CollectionSerializer(read_only=True)
    collection_id = serializers.PrimaryKeyRelatedField(
        queryset=models.Collection.objects.all(), write_only=True
    )

    class Meta:
        model = models.CollectionPermission
        fields = '__all__'


class ChecksumFileSerializer(serializers.ModelSerializer):
    """Serializer for ChecksumFiles.

    On POST, this can only handle URL files.
    """

    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['download_url'] = value.get_url()
        return ret

    class Meta:
        model = models.ChecksumFile
        fields = '__all__'
        read_only_fields = [
            'id',
            'checksum',
            'last_validation',
            'modified',
            'created',
            'status',
            'failure_reason',
        ]


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


class SpatialAssetSerializer(SpatialEntrySerializer):
    file = ChecksumFileSerializer(read_only=True)
    file_id = serializers.PrimaryKeyRelatedField(
        queryset=models.ChecksumFile.objects.all(), write_only=True
    )

    class Meta:
        model = models.SpatialAsset
        exclude = ['footprint', 'outline']


utility.make_serializers(globals(), models)
