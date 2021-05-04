from django.db import models


class AssetRole(models.Model):
    """The role used to describe the purpose of each asset."""

    name = models.TextField[str, str](
        unique=True,
        help_text="The name of the asset's role.",
    )
    description = models.TextField[str, str](
        help_text='Multi-line description to add further asset role information.',
    )

    def __str__(self):
        return self.name
