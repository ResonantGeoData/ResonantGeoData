from typing import Iterable

from rest_framework import serializers

from . import STACRasterFeatureSerializer
from .. import models


class STACRasterFeatureCollectionSerializer(serializers.BaseSerializer):
    def to_representation(self, items: Iterable[models.RasterMeta]) -> dict:
        return {
            'stac_version': '1.0.0',
            'stac_extensions': [
                'https://stac-extensions.github.io/eo/v1.0.0/schema.json',
                'https://stac-extensions.github.io/projection/v1.0.0/schema.json',
            ],
            'type': 'FeatureCollection',
            'features': [STACRasterFeatureSerializer(rastermeta).data for rastermeta in items],
        }
