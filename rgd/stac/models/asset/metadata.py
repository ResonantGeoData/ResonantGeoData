from datetime import datetime

from django.db import models


class Basics:
    title = models.TextField[str, str](help_text='A human readable title describing the Item.')
    description = models.TextField[str, str](
        help_text=(
            'Detailed multi-line description to fully explain the Item.'
            'CommonMark 0.29 syntax MAY be used for rich text representation.'
        )
    )


class DateAndTime:
    created = models.DateTimeField[datetime, datetime](
        help_text=('Creation date and time of the data linked to the Asset Object.')
    )
    updated = models.DateTimeField[datetime, datetime](
        help_text=(
            'Date and time the corresponding data linked to the Asset Object was updated last.'
        )
    )
