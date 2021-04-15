from django.db import models

from rgd.stac.models.asset.role import AssetRole
from rgd.stac.models.mediatype import MediaType


class AbstractAsset(models.Model):
    """
    An Asset is an object that contains a URI to data associated
    with the Item that can be downloaded or streamed. It is allowed
    to add additional fields.
    """

    type = models.ForeignKey[MediaType, MediaType](
        MediaType,
        on_delete=models.PROTECT,
        help_text='Media type of the asset',
    )
    title = models.TextField[str, str](
        help_text='The displayed title for clients and users.',
    )
    description = models.TextField[str, str](
        help_text=(
            'A description of the Asset providing additional details, '
            'such as how it was processed or created. CommonMark 0.29 '
            'syntax MAY be used for rich text representation.'
        ),
    )
    roles = models.ManyToManyField[AssetRole, AssetRole](
        AssetRole,
        related_name='assets',
        related_query_name='assets',
        help_text='The semantic roles of the asset, similar to the use of rel in links.',
    )

    class Meta:
        abstract = True


class Asset(AbstractAsset):
    pass
