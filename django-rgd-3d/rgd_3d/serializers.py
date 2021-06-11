import base64

from rest_framework import serializers
from rgd import utility
from rgd.serializers import ChecksumFileSerializer

from . import models


class PointCloudFileSerializer(serializers.ModelSerializer):
    file = ChecksumFileSerializer()

    class Meta:
        model = models.PointCloudFile
        fields = '__all__'


class PointCloudEntrySerializer(serializers.ModelSerializer):
    source = PointCloudFileSerializer()
    vtp_data = ChecksumFileSerializer()

    def to_representation(self, value):
        ret = super().to_representation(value)
        return ret

    class Meta:
        model = models.PointCloudEntry
        fields = '__all__'


class PointCloudEntryDataSerializer(PointCloudEntrySerializer):
    def to_representation(self, value):
        ret = super().to_representation(value)
        # Extract data as base64
        with value.vtp_data.yield_local_path() as path:
            with open(path, 'rb') as data:
                data_content = data.read()
                base64_content = base64.b64encode(data_content)
                base64_content = base64_content.decode().replace('\n', '')
        ret['vtp_data'] = base64_content
        return ret


utility.make_serializers(globals(), models)
