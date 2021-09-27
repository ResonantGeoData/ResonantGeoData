from typing import Iterable

from rest_framework import serializers
from rgd_imagery import models

from .item import ItemSerializer


class ItemCollectionSerializer(serializers.BaseSerializer):
    def to_representation(self, items: Iterable[models.RasterMeta]) -> dict:
        return {
            'type': 'FeatureCollection',
            'features': [ItemSerializer(rastermeta).data for rastermeta in items],
        }
