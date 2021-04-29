from django.db import models

from rgd.stac.models import Collection
from rgd.stac.models.extensions import ModelExtension


class CollectionKeywords(models.Model):
    """The roles field is used to describe the purpose of each asset."""

    name = models.TextField[str, str](
        unique=True,
        help_text="A keyword to describe the Collection.",
    )
    description = models.TextField[str, str](
        help_text='Multi-line description to add further asset keyword information.',
    )


collection = ModelExtension(
    title='Core Collection Fields',
    identifier='schemas.stacspec.org/v1.0.0-rc.2/collection-spec/json-schema/collection.json',
    prefix='core',
)


fields = {
    'keywords': models.ManyToManyField[CollectionKeywords, CollectionKeywords](
        CollectionKeywords,
        help_text='List of keywords describing the Collection.',
    ),
}

collection.extend_model(model=Collection, fields=fields)
