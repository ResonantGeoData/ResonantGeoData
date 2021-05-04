from django.db import models


class MediaType(models.Model):
    """A MIME type.

    Any media type can be used in an Item's asset ``type`` field, and registered
    Media Types are preferred. STAC Items that have sidecar metadata files
    associated with a data asset (e.g, .tfw, Landsat 8 MTL files) should use
    media types appropriate for the the metadata file. For example, if it is a
    plain text file, then text/plain would be appropriate; if it is an XML, then
    text/xml is appropriate.
    """

    name = models.TextField[str, str](
        unique=True,
        help_text='The MIME type label',
    )
    description = models.TextField[str, str](
        help_text='A multi-line description of the MIME type',
    )

    def __str__(self):
        return self.name
