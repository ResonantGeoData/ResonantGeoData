from django.db import models


class CollectionKeyword(models.Model):
    """Keyword describing Collections."""

    name = models.TextField[str, str](
        unique=True,
        help_text='A keyword to describe the Collection.',
    )
    description = models.TextField[str, str](
        help_text='Multi-line description to add further keyword information.',
    )

    def __str__(self):
        return self.name
