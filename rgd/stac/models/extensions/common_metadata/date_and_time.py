from datetime import datetime

from django.db import models

from rgd.stac.models import ItemProperty
from rgd.stac.models.extensions import ExtendableModel, ModelExtension

"""
Fields to provide additional temporal information such as ranges with a start
and an end datetime stamp.

`created` and `updated` have different meaning depending on where they are used.
If those fields are available in the Item properties, it's referencing to the
creation and update times of the metadata. Having those fields in the Item
assets refers to the creation and update times of the actual data linked to in
the Asset Object.
"""

date_and_time = ModelExtension(
    title='Date and Time Fields',
    identifier='schemas.stacspec.org/v1.0.0-rc.2/item-spec/json-schema/datetime.json',
    prefix='CommonDateAndTime',
)


def fields(model):
    return {
        'datetime': models.DateTimeField[datetime, datetime](
            help_text=('The searchable date and time of the metadata, in UTC.'),
            null=True,
        ),
        'created': models.DateTimeField[datetime, datetime](
            help_text=('Creation date and time the data.'),
            null=True,
        ),
        'updated': models.DateTimeField[datetime, datetime](
            help_text=('Date and time the data was updated last.'),
            null=True,
        ),
        'start_datetime': models.DateTimeField[datetime, datetime](
            help_text=('The first or start date and time for the Item, in UTC.'),
            null=True,
        ),
        'end_datetime': models.DateTimeField[datetime, datetime](
            help_text=('The last or end date and time for the Item, in UTC.'),
            null=True,
        ),
    }


def opts(model):
    return {
        'constraints': [
            models.CheckConstraint(
                check=(
                    models.Q(datetime__isnull=False)
                    | (
                        models.Q(end_datetime__isnull=False)
                        & models.Q(start_datetime__isnull=False)
                    )
                ),
                name='%(class)s_include_time',
            )
        ]
        if model == ItemProperty
        else []
    }


for model in ExtendableModel.get_children():
    date_and_time.extend_model(model=model, fields=fields(model), opts=opts(model))
