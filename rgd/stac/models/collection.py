from django.db import models

from rgd.stac.models.extensions import ExtendableModel


class Collection(ExtendableModel):
    """A STAC Collection object is used to describe a group of related Items.

    It builds on fields defined for a Catalog object by further defining and
    explaining logical groups of Items. A Collection can have parent Catalog and
    Collection objects, as well as child Item, Catalog, and Collection objects.
    These parent-child relationships among objects of these types, as there is
    no subtyping relationship between the Collection and Catalog types, even
    through they share field names.

    IMPORTANT: This specific implementation of STAC interprets a special meaning
    of a Collection that is not explicitly stated in the official STAC
    specification: a Collection is relational to other Collections. This follows
    the logic stated in the STAC specification that an Item must only be in one
    Collection. WE IMPOSE THE REQUIREMENT THAT A COLLECTION MUST ONLY BE IN ONE
    COLLECTION. This child/parent relationship between Collections may be
    "interupted" by Catalogs in a free-form fashion.
    """

    parent = models.ForeignKey['Collection', 'Collection'](
        'self',
        on_delete=models.CASCADE,
        help_text='The parent Collection or `NULL` if this Collection is a root.',
    )
