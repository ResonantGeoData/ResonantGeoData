import os

from django.db import IntegrityError
import pytest
from rgd.datastore import datastore, registry
from rgd.models import common

FILENAME = 'stars.png'


@pytest.fixture
def file_path():
    return datastore.fetch(FILENAME)


@pytest.mark.django_db(transaction=True)
def test_checksumfile_file_create(file_path):
    model = common.ChecksumFile()
    model.type = common.FileSourceType.FILE_FIELD
    with open(file_path, 'rb') as f:
        model.file.save(FILENAME, f)
    model.save()
    model.post_save_job()
    model.refresh_from_db()
    assert model.checksum == registry[FILENAME].split(':')[1]
    assert model.name == FILENAME


@pytest.mark.django_db(transaction=True)
def test_checksumfile_url_create():
    model = common.ChecksumFile()
    model.type = common.FileSourceType.URL
    model.url = datastore.get_url(FILENAME)
    model.save()
    model.post_save_job()
    model.refresh_from_db()
    assert model.checksum == registry[FILENAME].split(':')[1]
    assert model.name


@pytest.mark.django_db(transaction=True)
def test_checksumfile_constraint_mismatch_a():
    with pytest.raises(IntegrityError):
        model = common.ChecksumFile()
        model.type = common.FileSourceType.FILE_FIELD
        model.url = datastore.get_url(FILENAME)
        model.save()


@pytest.mark.django_db(transaction=True)
def test_checksumfile_constraint_mismatch_b(file_path):
    with pytest.raises(IntegrityError):
        model = common.ChecksumFile()
        model.type = common.FileSourceType.URL
        with open(file_path, 'rb') as f:
            model.file.save(FILENAME, f)


@pytest.mark.django_db(transaction=True)
def test_checksumfile_constraint_url_null():
    with pytest.raises(IntegrityError):
        model = common.ChecksumFile()
        model.type = common.FileSourceType.URL
        model.save()


@pytest.mark.django_db(transaction=True)
def test_checksumfile_constraint_url_empty():
    with pytest.raises(IntegrityError):
        model = common.ChecksumFile()
        model.type = common.FileSourceType.URL
        model.url = ''
        model.save()


@pytest.mark.django_db(transaction=True)
def test_checksumfile_constraint_file_with_empty_url(file_path):
    # Make sure the constraint passes when an empty string URL is given with
    #   the FileField choice. This happens when adding files in the admin interface
    model = common.ChecksumFile()
    model.type = common.FileSourceType.FILE_FIELD
    model.url = ''
    with open(file_path, 'rb') as f:
        model.file.save(FILENAME, f)
    assert not model.url
    assert model.file.name


@pytest.mark.django_db(transaction=True)
def test_checksumfile_file_yield_local_path(file_path):
    model = common.ChecksumFile()
    model.type = common.FileSourceType.FILE_FIELD
    with open(file_path, 'rb') as f:
        model.file.save(FILENAME, f)
    model.save()
    path = model.yield_local_path()
    with model.yield_local_path() as path:
        assert os.path.exists(path)
    # Make sure it is cleaned up after context ends
    assert not os.path.exists(path)
    # Now test that is gets cleaned up during an exception
    with pytest.raises(ValueError):
        with model.yield_local_path() as path:
            raise ValueError()
    assert not os.path.exists(path)


@pytest.mark.django_db(transaction=True)
def test_checksumfile_url_yield_local_path():
    model = common.ChecksumFile()
    model.type = common.FileSourceType.URL
    model.url = datastore.get_url(FILENAME)
    model.save()
    with model.yield_local_path() as path:
        assert os.path.exists(path)
    # Make sure it is cleaned up after context ends
    assert not os.path.exists(path)
    # Now test that is gets cleaned up during an exception
    with pytest.raises(ValueError):
        with model.yield_local_path() as path:
            raise ValueError()
    assert not os.path.exists(path)
