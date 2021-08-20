import json

from rest_framework import serializers

from . import models, utility

MODIFIABLE_READ_ONLY_FIELDS = ['modified', 'created']
TASK_EVENT_READ_ONLY_FIELDS = ['status', 'failure_reason']
SPATIAL_ENTRY_EXCLUDE = ['footprint', 'outline']


class RelatedField(serializers.PrimaryKeyRelatedField):
    """Handle GET/POST in a single field.

    Reference: https://stackoverflow.com/a/52246232
    """

    def __init__(self, **kwargs):
        self.serializer = kwargs.pop('serializer', None)
        if self.serializer is not None and not issubclass(self.serializer, serializers.Serializer):
            raise TypeError('"serializer" is not a valid serializer class')

        super().__init__(**kwargs)

    def use_pk_only_optimization(self):
        return False if self.serializer else True

    def to_representation(self, instance):
        if self.serializer:
            return self.serializer(instance, context=self.context).data
        return super().to_representation(instance)


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Collection
        fields = '__all__'


class CollectionPermissionSerializer(serializers.ModelSerializer):
    collection = RelatedField(
        queryset=models.Collection.objects.all(), serializer=CollectionSerializer
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
        read_only_fields = (
            [
                'checksum',
                'last_validation',
            ]
            + MODIFIABLE_READ_ONLY_FIELDS
            + TASK_EVENT_READ_ONLY_FIELDS
        )


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
        exclude = SPATIAL_ENTRY_EXCLUDE


class SpatialEntryFootprintSerializer(SpatialEntrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        ret['footprint'] = json.loads(value.footprint.geojson)
        return ret

    class Meta:
        model = models.SpatialEntry
        exclude = SPATIAL_ENTRY_EXCLUDE


class SpatialAssetSerializer(SpatialEntrySerializer):
    file = RelatedField(
        queryset=models.ChecksumFile.objects.all(), serializer=ChecksumFileSerializer
    )

    class Meta:
        model = models.SpatialAsset
        exclude = SPATIAL_ENTRY_EXCLUDE


utility.make_serializers(globals(), models)
