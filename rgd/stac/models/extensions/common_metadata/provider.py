from django.db import models

from rgd.stac.models.extensions import ExtendableModel, ModelExtension

"""
Information about the organizations capturing, producing, processing, hosting or
publishing this data. Provider information should be defined at the Collection
level if possible.

The `ProviderObject` provides information about a provider. A provider is any of
the organizations that captures or processes the content of the assets and
therefore influences the data offered by the STAC implementation. May also
include information about the final storage provider hosting the data.
"""


class ProviderRole(models.Model):
    name = models.TextField[str, str](
        unique=True,
        help_text="The name of the organization's or the individual's role.",
    )
    description = models.TextField[str, str](
        help_text='Multi-line description to add further provider role information.',
    )


class ProviderObject(models.Model):
    name = models.TextField[str, str](
        unique=True,
        help_text='The name of the organization or the individual.',
    )
    description = models.TextField[str, str](
        blank=True,
        help_text=(
            'Multi-line description to add further provider information such as '
            'processing details for processors and producers, hosting details for'
            'hosts or basic contact information. CommonMark 0.29 syntax may be '
            'used for rich text representation.'
        ),
    )
    roles = models.ManyToManyField[ProviderRole, ProviderRole](
        ProviderRole, help_text='Roles of the provider.'
    )
    url = models.URLField[str, str](blank=True)


provider = ModelExtension(
    title='Provider',
    identifier='schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/provider.json',
    prefix='CommonProvider',
)


def fields(model: ExtendableModel):
    return {
        'providers': models.ManyToManyField[ProviderObject, ProviderObject](
            ProviderObject,
            help_text=(
                'A list of providers, which may include all organizations capturing or '
                'processing the data or the hosting provider.'
            ),
        ),
    }


def opts(model: ExtendableModel):
    return {}


for model in ExtendableModel.get_children():
    provider.extend_model(model=model, fields=fields(model), opts=opts(model))
