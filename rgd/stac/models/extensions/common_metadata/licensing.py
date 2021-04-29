from django.db import models

from rgd.stac.models.extensions import ExtendableModel, ModelExtension

"""
Information about the license(s) of the data, which is not necessarily the same
license that applies to the metadata. Licensing information should be defined at
the Collection level if possible.

    `license`: Data license(s) as a SPDX License identifier. Alternatively, use
    proprietary (see below) if the license is not on the SPDX license list or
    various if multiple licenses apply. In all cases links to the license texts
    SHOULD be added, see the license link relation type. If no link to a license is
    included and the license field is set to proprietary, the Collection is private,
    and consumers have not been granted any explicit right to use the data.
"""


class License(models.Model):
    name = models.TextField[str, str](
        unique=True,
        help_text='Data license(s) as a SPDX License identifier.',
    )
    content = models.TextField[str, str](
        help_text='The license content.',
    )


licensing = ModelExtension(
    title='Licensing Fields',
    identifier='schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/licensing.json',
    prefix='CommonLicensing',
)


def fields(model: ExtendableModel):
    return {
        'licenses': models.ManyToManyField[License, License](
            License,
            help_text='Unique name of the specific platform to which the instrument is attached.',
        ),
    }


def opts(model: ExtendableModel):
    return {}


for model in ExtendableModel.get_children():
    licensing.extend_model(model=model, fields=fields(model), opts=opts(model))
