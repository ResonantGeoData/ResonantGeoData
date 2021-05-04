from django.db import models

from rgd.stac.models import Collection
from rgd.stac.models.extensions import ModelExtension

from .models import CollectionKeyword

collection = ModelExtension(
    title='Core Collection Fields',
    identifier='schemas.stacspec.org/v1.0.0-rc.2/collection-spec/json-schema/collection.json',
    prefix='core',
)


fields = {
    'keywords': models.ManyToManyField[CollectionKeyword, CollectionKeyword](
        CollectionKeyword,
        help_text='List of keywords describing the Collection.',
    ),
}

collection.extend_model(model=Collection, fields=fields)
