from django.db import models

from rgd.stac.models import Catalog, Collection, Item
from rgd.stac.models.extensions import ExtendableModel


class LinkRelType(models.Model):
    name = models.TextField[str, str](unique=True)
    description = models.TextField[str, str]()


class Link(ExtendableModel):
    """This object describes a relationship with another entity.

    Data providers are advised to be liberal with the links section, to describe
    things like the Catalog an Item is in, related Items, parent or child Items
    (modeled in different ways, like an 'acquisition' or derived data).
    """

    left_item = models.ForeignKey[Item, Item](
        Item,
        on_delete=models.CASCADE,
        null=True,
        related_name='links',
    )
    left_catalog = models.ForeignKey[Catalog, Catalog](
        Catalog,
        on_delete=models.CASCADE,
        null=True,
        related_name='links',
    )
    left_collection = models.ForeignKey[Collection, Collection](
        Collection,
        on_delete=models.CASCADE,
        null=True,
        related_name='links',
    )
    reltype = models.ForeignKey[LinkRelType, LinkRelType](
        LinkRelType,
        on_delete=models.CASCADE,
        related_name='+',
    )
    right_item = models.ForeignKey[Item, Item](
        Item,
        on_delete=models.CASCADE,
        null=True,
        related_name='+',
    )
    right_catalog = models.ForeignKey[Catalog, Catalog](
        Catalog,
        on_delete=models.CASCADE,
        null=True,
        related_name='+',
    )
    right_collection = models.ForeignKey[Collection, Collection](
        Collection,
        on_delete=models.CASCADE,
        null=True,
        related_name='+',
    )
