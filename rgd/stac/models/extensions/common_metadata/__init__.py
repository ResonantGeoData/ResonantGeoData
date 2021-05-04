"""Extends the STAC wireframe with 'STAC Common Metadata'.

STAC Common Metadata extends all extendable objects with attributes. Although
the attributes can be placed on any object, they are most often found used in
STAC Item properties.

https://github.com/radiantearth/stac-spec/blob/master/item-spec/common-metadata.md
"""

from .basics import basics
from .date_and_time import date_and_time
from .instrument import instrument
from .licensing import licensing
from .provider import provider

__all__ = ['basics', 'date_and_time', 'instrument', 'licensing', 'provider']
