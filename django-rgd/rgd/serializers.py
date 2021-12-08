import json

from rest_framework import serializers

from . import models

MODIFIABLE_READ_ONLY_FIELDS = ['modified', 'created']
TASK_EVENT_READ_ONLY_FIELDS = ['status', 'failure_reason']
SPATIAL_ENTRY_EXCLUDE = ['footprint']


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


class ChecksumFileFolderSerializer(serializers.Serializer):
    known_size = serializers.IntegerField()
    num_files = serializers.IntegerField()
    num_url_files = serializers.IntegerField()
    created = serializers.DateTimeField()
    modified = serializers.DateTimeField()


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


class ChecksumFilePathQuerySerializer(serializers.Serializer):
    path_prefix = serializers.CharField(required=False)


class ChecksumFilePathsSerializer(serializers.Serializer):
    folders = serializers.DictField(child=ChecksumFileFolderSerializer())
    files = serializers.DictField(child=ChecksumFileSerializer())


class SpatialEntrySerializer(serializers.ModelSerializer):
    outline = serializers.SerializerMethodField()
    subentry_name = serializers.SerializerMethodField()
    subentry_type = serializers.SerializerMethodField()

    class Meta:
        model = models.SpatialEntry
        exclude = SPATIAL_ENTRY_EXCLUDE

    def get_outline(self, obj):
        return json.loads(obj.outline.geojson)

    def get_subentry_type(self, obj):
        return type(obj).__name__

    def get_subentry_name(self, obj):
        return getattr(obj, 'name', None)


class SpatialEntryFootprintSerializer(SpatialEntrySerializer):
    footprint = serializers.SerializerMethodField()

    class Meta:
        model = models.SpatialEntry
        fields = '__all__'

    def get_footprint(self, obj):
        return json.loads(obj.footprint.geojson)


class SpatialAssetSerializer(SpatialEntrySerializer):
    file = RelatedField(
        queryset=models.ChecksumFile.objects.all(), serializer=ChecksumFileSerializer
    )

    class Meta:
        model = models.SpatialAsset
        exclude = SPATIAL_ENTRY_EXCLUDE
