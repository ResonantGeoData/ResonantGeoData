from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.postgres.fields import DateTimeRangeField
from django.db import models

from rgd.stac.models import Collection
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

    Additional metadata fields can be added to the GeoJSON Object Properties.

    The only required field is datetime (or start_datetime+end_datetime) but it
    is recommended to add more fields.
    """

    collection = models.ForeignKey[Collection, Collection](
        Collection,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Each item belongs to a single collection.',
    )
    geometry = GeometryField(
        help_text=(
            'Defines the full footprint of the asset represented by this item, '
            'formatted according to RFC 7946, section 3.1. The footprint should '
            'be the default GeoJSON geometry, though additional geometries can '
            'be included. Coordinates are specified in Longitude/Latitude or '
            'Longitude/Latitude/Elevation based on WGS 84.'
        ),
    )
    datetime = DateTimeRangeField(
        help_text='The searchable date and time of the metadata.',
    )
