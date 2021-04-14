from django.contrib.gis.db.models import GeometryField
from django.core import checks
from django.db import models
from django.db.models.deletion import CASCADE

from rgd.stac.models.asset import AbstractAsset, Asset
from rgd.stac.models.properties import AbstractProperties, Properties


class AbstractItem(models.Model):
    """
    This document explains the structure and content of a SpatioTemporal Asset Catalog (STAC) Item.
    An Item is a GeoJSON Feature augmented with foreign members relevant to a STAC object. These
    include fields that identify the time range and assets of the Item. An Item is the core object
    in a STAC Catalog, containing the core metadata that enables any client to search or crawl
    online catalogs of spatial 'assets' (e.g., satellite imagery, derived data, DEMs).

    The same Item definition is used in both STAC Catalogs and the Item-related API endpoints.
    Catalogs are simply sets of Items that are linked online, generally served by simple web servers
    and used for crawling data. The search endpoint enables dynamic queries, for example selecting
    all Items in Hawaii on June 3, 2015, but the results they return are FeatureCollections of Items.

    Items are represented in JSON format and are very flexible. Any JSON object that contains all the
    required fields is a valid STAC Item.
    """

    geometry = GeometryField()
    properties = models.OneToOneField[Properties, Properties](Properties, on_delete=CASCADE)
    assets = models.ManyToManyField[Asset, Asset](Asset)

    @classmethod
    def check(cls, **kwargs):
        errors = [
            *super().check(**kwargs),
            *cls._check_properties(),
            *cls._check_assets(),
        ]
        return errors

    @classmethod
    def _check_properties(cls):
        if (
            not hasattr(cls, 'properties')
            or not isinstance(cls.properties, models.OneToOneField)
            or not isinstance(cls.properties.target_field, AbstractProperties)
        ):
            return [
                checks.Error(
                    "'properties' field missing",
                    obj=cls,
                    id='stac.E001',
                )
            ]
        return []

    @classmethod
    def _check_assets(cls):
        if (
            not hasattr(cls, 'assets')
            or not isinstance(cls.assets, models.ManyToManyField)
            or not isinstance(cls.properties.target_field, AbstractAsset)
        ):
            return [
                checks.Warning(
                    "'assets' field missing",
                    obj=cls,
                    id='stac.E001',
                )
            ]
        return []

    class Meta:
        abstract = True


class Item(AbstractItem):
    pass
