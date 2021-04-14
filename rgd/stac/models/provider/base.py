from django.db import models

from rgd.stac.models.provider.role import ProviderRole


class Provider(models.Model):
    """
    The object provides information about a provider. A provider is any of the organizations
    that captures or processes the content of the assets and therefore influences the data
    offered by the STAC implementation. May also include information about the final storage
    provider hosting the data.
    """

    name = models.TextField[str, str](help_text='The name of the organization or the individual.')
    description = models.TextField[str, str](
        help_text=(
            'Multi-line description to add further provider information such as processing details '
            'for processors and producers, hosting details for hosts or basic contact information. '
            'CommonMark 0.29 syntax MAY be used for rich text representation.'
        )
    )
    roles = models.ManyToManyField[ProviderRole, ProviderRole](
        ProviderRole,
        help_text="Roles of the provider. Any of 'licensor', 'producer', 'processor' or 'host'.",
    )
