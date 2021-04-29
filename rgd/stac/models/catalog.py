from rgd.stac.models.extensions import ExtendableModel


class Catalog(ExtendableModel):
    """A STAC Catalog object represents a logical group of other Catalog, Collection, and Item objects.

    These Items can be linked to directly from a
    Catalog, or the Catalog can link to other Catalogs (often called
    sub-catalogs) that contain links to Collections and Items. The division of
    sub-catalogs is up to the implementor, but is generally done to aid the ease
    of online browsing by people.
    """

    pass
