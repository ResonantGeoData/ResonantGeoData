from django.db import models

from rgd.stac.models import Collection, Item
from rgd.stac.models.extensions import ExtendableModel


class Asset(ExtendableModel):
    """An object that contains a URI to data associated with the Item/Collection that can be downloaded or streamed."""

    items = models.ManyToManyField[Item, Item](
        Item,
        through='AssetToItem',
        related_name='assets',
        help_text='Items associated with this asset.',
    )
    collections = models.ManyToManyField[Collection, Collection](
        Collection,
        through='AssetToCollection',
        related_name='assets',
        help_text='Collections associated with this asset.',
    )


class AssetToItem(models.Model):
    """Through table for unique `key`."""

    item = models.ForeignKey[Item, Item](
        Item,
        related_name='+',
        on_delete=models.CASCADE,
    )
    asset = models.ForeignKey[Asset, Asset](
        Asset,
        related_name='+',
        on_delete=models.CASCADE,
    )
    key = models.TextField[str, str]()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['item', 'asset', 'key'],
                name='assettoitem_unique_key',
            )
        ]


class AssetToCollection(models.Model):
    """Through table for unique `key`."""

    collection = models.ForeignKey[Collection, Collection](
        Collection,
        related_name='+',
        on_delete=models.CASCADE,
    )
    asset = models.ForeignKey[Asset, Asset](
        Asset,
        related_name='+',
        on_delete=models.CASCADE,
    )
    key = models.TextField[str, str]()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['collection', 'asset', 'key'],
                name='assettocollection_unique_key',
            )
        ]
