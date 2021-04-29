from django.db import models


class MediaType(models.Model):
    """
    Any media type can be used in an Item's asset ``type`` field,
    and registered Media Types are preferred. STAC Items that have
    sidecar metadata files associated with a data asset (e.g, .tfw,
    Landsat 8 MTL files) should use media types appropriate for
    the the metadata file. For example, if it is a plain text file,
    then text/plain would be appropriate; if it is an XML, then
    text/xml is appropriate. For more information on media types
    as well as a list of common media types used in STAC see the
    best practice on working with media types.
    """

    term = models.TextField[str, str](unique=True)
    description = models.TextField[str, str]()
