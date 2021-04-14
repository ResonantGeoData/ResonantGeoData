from django.core.exceptions import ValidationError
from django.db import models


def validate_choices(value: str):
    if value not in {'licensor', 'producer', 'processor', 'host'}:
        raise ValidationError(
            "'%(value)s' invalid. Must be one of 'licensor', 'producer', 'processor', or 'host'",
            params={'value': value},
        )


class ProviderRole(models.Model):
    """
    Roles of the provider. Any of ``licensor``, ``producer``, ``processor`` or ``host``.
    """

    slug = models.SlugField[str, str](validators=[validate_choices])
    description = models.TextField[str, str]()
