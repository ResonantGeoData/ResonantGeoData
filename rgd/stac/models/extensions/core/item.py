from django.contrib.gis.db import models

from rgd.stac.models import Item
from rgd.stac.models.extensions import ModelExtension

item = ModelExtension(
    title='Core Item Fields',
    identifier='schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json',
    prefix='core',
)


fields = {
    'geometry': models.GeometryField(
        help_text=(
            'Defines the full footprint of the asset represented by this item, '
            'formatted according to RFC 7946, section 3.1. The footprint should '
            'be the default GeoJSON geometry, though additional geometries can '
            'be included. Coordinates are specified in Longitude/Latitude or '
            'Longitude/Latitude/Elevation based on WGS 84.'
        ),
        null=True,
    ),
}

item.extend_model(model=Item, fields=fields)
