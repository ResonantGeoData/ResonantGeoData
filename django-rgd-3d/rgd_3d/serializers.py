import base64

from rest_framework import serializers
from rgd.serializers import ChecksumFileSerializer
from rgd_3d import models


class Mesh3DSerializer(serializers.ModelSerializer):
    file = ChecksumFileSerializer()

    class Meta:
        model = models.Mesh3D
        fields = '__all__'


class Mesh3DMetaSerializer(serializers.ModelSerializer):
    source = Mesh3DSerializer()
    vtp_data = ChecksumFileSerializer(required=False)

    def to_representation(self, value):
        ret = super().to_representation(value)
        return ret

    class Meta:
        model = models.Mesh3DMeta
        fields = '__all__'


class Mesh3DMetaDataSerializer(Mesh3DMetaSerializer):
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
