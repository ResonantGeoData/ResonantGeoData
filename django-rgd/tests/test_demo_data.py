import pytest

from rgd.datastore import registry
from rgd.management.commands import demo_data


def test_entries_in_datastore():
    def is_in_datastore(f):
        if isinstance(f, (list, tuple)):
            return all([is_in_datastore(i) for i in f])
        return f in registry

    for f in (
        demo_data.RASTER_FILES
        + demo_data.SHAPE_FILES
        + demo_data.FMV_FILES
        + demo_data.KWCOCO_ARCHIVES
    ):
        assert is_in_datastore(f), f'`{f}` not in registry.'
