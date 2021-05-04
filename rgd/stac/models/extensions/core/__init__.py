"""Extends the STAC wireframe with minimum fields defined in the 'core' definition.

Any fields that could be calculated are not included. It is assumed that all
assets are downloaded when ingested so that URLs can be dynamically generated.
This follows STAC 'best practices'.


https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md
https://github.com/radiantearth/stac-spec/blob/master/collection-spec/collection-spec.md
"""

from .asset import asset
from .collection import collection
from .item import item

__all__ = ['asset', 'collection', 'item']
