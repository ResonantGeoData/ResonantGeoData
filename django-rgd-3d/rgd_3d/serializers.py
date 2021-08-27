import base64

from rest_framework import serializers
from rgd import utility
from rgd.serializers import ChecksumFileSerializer
from rgd_3d import models


class PointCloudSerializer(serializers.ModelSerializer):
    file = ChecksumFileSerializer()

    class Meta:
        model = models.PointCloud
        fields = '__all__'


class PointCloudMetaSerializer(serializers.ModelSerializer):
    source = PointCloudSerializer()
    vtp_data = ChecksumFileSerializer(required=False)

    def to_representation(self, value):
        ret = super().to_representation(value)
        return ret

    class Meta:
        model = models.PointCloudMeta
        fields = '__all__'


class PointCloudMetaDataSerializer(PointCloudMetaSerializer):
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
