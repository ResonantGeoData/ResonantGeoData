from django.db import models

from rgd.stac.models import Catalog, Collection
from rgd.stac.models.extensions import ExtendableModel, ModelExtension

"""
Descriptive fields to give a basic overview of a STAC Item.
"""

basics = ModelExtension(
    title='Basic Descriptive Fields',
    identifier='schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/basics.json',
    prefix='CommonBasics',
)


def fields(model: ExtendableModel):
    return {
        'title': models.TextField[str, str](
            help_text='A human readable title.',
            null=False,
        ),
        'description': models.TextField[str, str](
            help_text=(
                'Detailed multi-line description. '
                'CommonMark 0.29 syntax MAY be used for rich text representation.'
            ),
            null=(model not in (Catalog, Collection)),
        ),
    }


def opts(model: ExtendableModel):
    return {}


for model in ExtendableModel.get_children():
    basics.extend_model(model=model, fields=fields(model), opts=opts(model))
