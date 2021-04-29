from django.db import models

from rgd.stac.models import Asset
from rgd.stac.models.extensions import ExtendableModel


class CollectionAsset(models.Model):
    """Through table for unique `key`."""

    collection = models.ForeignKey['Collection', 'Collection'](
        'Collection',
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
                name='collectionasset_unique_key',
            )
        ]


class Collection(ExtendableModel):
    """A STAC Collection object is used to describe a group of related Items.

    It builds on fields defined for a Catalog object by further defining and explaining
    logical groups of Items. A Collection can have parent Catalog and Collection
    objects, as well as child Item, Catalog, and Collection objects. These
    parent-child relationships among objects of these types, as there is no
    subtyping relationship between the Collection and Catalog types, even through
    they share field names.
    """

    assets = models.ManyToManyField[Asset, Asset](
        Asset,
        through=CollectionAsset,
        related_name='collections',
    )
