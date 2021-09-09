from typing import Iterable

from rest_framework import serializers

from .item import ItemSerializer
from rgd_imagery import models


class ItemCollectionSerializer(serializers.BaseSerializer):
    def to_representation(self, items: Iterable[models.RasterMeta]) -> dict:
        return {
            'type': 'FeatureCollection',
            'features': [ItemSerializer(rastermeta).data for rastermeta in items],
        }
