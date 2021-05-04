from django.db import models

from rgd.stac.models import Asset
from rgd.stac.models.extensions import ExtendableModel


class Item(ExtendableModel):
    """A GeoJSON Feature augmented with foreign members relevant to a STAC object.

    These include fields that identify the time range and assets of
    the Item. An Item is the core object in a STAC Catalog, containing the core
    metadata that enables any client to search or crawl online catalogs of
    spatial 'assets' (e.g., satellite imagery, derived data, DEMs).

    The same Item definition is used in both STAC Catalogs and the Item-related
    API endpoints. Catalogs are simply sets of Items that are linked online,
    generally served by simple web servers and used for crawling data. The
    search endpoint enables dynamic queries, for example selecting all Items in
    Hawaii on June 3, 2015, but the results they return are FeatureCollections
    of Items.

    Items are represented in JSON format and are very flexible. Any JSON object
    that contains all the required fields is a valid STAC Item.


class ItemProperty(ExtendableModel):
    """Additional metadata fields can be added to the GeoJSON Object Properties.

    The only required field is datetime but it is recommended to add more
    fields, see Additional Fields resources below.
    """

    item = models.OneToOneField[Item, Item](
        Item,
        on_delete=models.CASCADE,
        related_name='properties',
    )
