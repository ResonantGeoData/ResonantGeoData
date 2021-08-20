from datetime import datetime
from typing import Literal, Tuple, Union

DATETIME_OR_STR_TUPLE = Tuple[Union[datetime, str], Union[datetime, str]]
SEARCH_PREDICATE_CHOICE = Literal[
    'contains',
    'crosses',
    'disjoint',
    'equals',
    'intersects',
    'overlaps',
    'touches',
    'within',
]
PROCESSED_IMAGE_TYPES = Literal[
    'arbitrary',
    'cog',
    'region',
    'resample',
    'mosaic',
]
