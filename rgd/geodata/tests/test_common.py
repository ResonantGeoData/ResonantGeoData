from django.db import IntegrityError
import pytest

from rgd.geodata.datastore import datastore, registry
from rgd.geodata.models import common

FILENAME = 'stars.png'


@pytest.mark.django_db(transaction=True)
def test_checksumfile_file():
    path = datastore.fetch(FILENAME)
    model = common.ChecksumFile()
    model.type = common.FileSourceType.FILE_FIELD
    model.file.save(FILENAME, open(path, 'rb'))
    model.save()
    assert model.checksum == registry[FILENAME].split(':')[1]
    assert model.name


@pytest.mark.django_db(transaction=True)
def test_checksumfile_url():
    model = common.ChecksumFile()
    model.type = common.FileSourceType.URL
    model.url = datastore.get_url(FILENAME)
    model.save()
    assert model.checksum == registry[FILENAME].split(':')[1]
    assert model.name


@pytest.mark.django_db(transaction=True)
def test_checksumfile_constraint():
    with pytest.raises(IntegrityError):
        model = common.ChecksumFile()
        model.name = 'foo'
        model.type = common.FileSourceType.FILE_FIELD
        model.url = datastore.get_url(FILENAME)
        model.save()
    with pytest.raises(IntegrityError):
        path = datastore.fetch(FILENAME)
        model = common.ChecksumFile()
        model.name = 'foo'
        model.type = common.FileSourceType.URL
        model.file.save(FILENAME, open(path, 'rb'))
