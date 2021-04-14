from datetime import datetime

from django.core import checks
from django.db import models


class AbstractProperties(models.Model):
    @classmethod
    def check(cls, **kwargs):
        errors = [
            *super().check(**kwargs),
            *cls._check_datetime(),
            *cls._check_providers(),
        ]
        return errors

    @classmethod
    def _check_datetime(cls):
        if not hasattr(cls, 'datetime') or (
            not hasattr(cls, 'start_datetime') or not hasattr(cls, 'end_datetime')
        ):
            return [
                checks.Error(
                    "'datetime', or 'start_datetime'/'end_datetime' fields missing",
                    hint="See mixins in 'stac.properties.common' for convenience",
                    obj=cls,
                    id='stac.E001',
                )
            ]
        return []

    @classmethod
    def _check_providers(cls):
        if hasattr(cls, 'providers'):
            return [
                checks.Warning(
                    'provider information should be defined at the Collection level if possible',
                    hint="See mixins in 'stac.properties.common' for convenience",
                    obj=cls,
                    id='stac.W001',
                )
            ]
        return []

    class Meta:
        abstract = True


class Properties(AbstractProperties):
    datetime = models.DateTimeField[datetime, datetime](
        help_text=(
            'The searchable date and time of the assets, in UTC. It is '
            'formatted according to RFC 3339, section 5.6.'
        ),
    )
