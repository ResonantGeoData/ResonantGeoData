from datetime import datetime

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MinValueValidator
from django.db import models

from rgd.stac.models.provider import Provider as ProviderModel


class Basics:
    """Descriptive fields to give a basic overview of a STAC Item."""

    title = models.TextField[str, str](help_text='A human readable title describing the Item.')
    description = models.TextField[str, str](
        help_text=(
            'Detailed multi-line description to fully explain the Item.'
            'CommonMark 0.29 syntax MAY be used for rich text representation.'
        )
    )


class Log:
    """
    ``created`` and ``updated`` have different meaning depending on where they are used.
    If those fields are available in the Item ``properties``, it's referencing to the
    creation and update times of the metadata. Having those fields in the Item ``assets``
    refers to the creation and update times of the actual data linked to in the
    Asset Object.
    """

    created = models.DateTimeField[datetime, datetime](
        help_text=('Creation date and time of the metadata.')
    )
    updated = models.DateTimeField[datetime, datetime](
        help_text=('Date and time the corresponding metadata was updated last.')
    )


class DateAndTimeRange:
    """Fields to provide additional temporal information such as ranges with a start and an end datetime stamp."""

    start_datetime = models.DateTimeField[datetime, datetime](
        help_text=('The first or start date and time for the Item, in UTC.')
    )
    end_datetime = models.DateTimeField[datetime, datetime](
        help_text=('The last or end date and time for the Item, in UTC.')
    )


class Provider:
    """
    Information about the organizations capturing, producing, processing, hosting or publishing this data.
    """

    providers = models.ManyToManyField[ProviderModel, ProviderModel](
        ProviderModel,
        help_text=(
            'A list of providers, which may include all organizations capturing or processing the '
            'data or the hosting provider. Providers should be listed in chronological order with '
            'the most recent provider being the last element of the list.'
        ),
    )


class Instrument:
    platform = models.TextField[str, str](
        help_text='Unique name of the specific platform to which the instrument is attached.'
    )
    instruments = ArrayField[str, str](
        models.TextField[str, str](),
        help_text='Name of instrument or sensor used (e.g., MODIS, ASTER, OLI, Canon F-1).',
    )
    constellation = models.TextField[str, str](
        help_text='Name of the constellation to which the platform belongs.'
    )
    mission = models.TextField[str, str](
        help_text='Name of the mission for which data is collected.'
    )
    gsd = models.FloatField[str, str](
        validators=[MinValueValidator(0)],
        help_text='Ground Sample Distance at the sensor, in meters (m).',
    )
