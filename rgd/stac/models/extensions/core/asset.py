from django.db import models

from rgd.stac.models import Asset
from rgd.stac.models.extensions import ModelExtension

from .models import AssetRole, MediaType

asset = ModelExtension(
    title='Core Asset Fields',
    identifier='schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/item.json',
    prefix='core',
)


fields = {
    'href': models.URLField[str, str](
        help_text='URI to the asset object.',
    ),
    'type': models.ForeignKey[MediaType, MediaType](
        MediaType,
        on_delete=models.PROTECT,
    ),
    'roles': models.ManyToManyField[AssetRole, AssetRole](
        AssetRole,
    ),
}

asset.extend_model(model=Asset, fields=fields)
