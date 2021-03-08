import os

from django.db import IntegrityError
import pytest

from rgd.geodata.datastore import datastore, registry
from rgd.geodata.models import common
from rgd.utility import precheck_fuse

FILENAME = 'stars.png'

try:
    import simple_httpfs  # noqa

    HAS_FUSE = True
except (ImportError, OSError):
    HAS_FUSE = False


@pytest.fixture
def file_path():
    return datastore.fetch(FILENAME)


@pytest.mark.django_db(transaction=True)
def test_checksumfile_file_create(file_path):
    model = common.ChecksumFile()
    model.type = common.FileSourceType.FILE_FIELD
    model.file.save(FILENAME, open(file_path, 'rb'))
    model.save()
    model.refresh_from_db()
    assert model.checksum == registry[FILENAME].split(':')[1]
    assert model.name == FILENAME


@pytest.mark.django_db(transaction=True)
def test_checksumfile_url_create():
    model = common.ChecksumFile()
    model.type = common.FileSourceType.URL
    model.url = datastore.get_url(FILENAME)
    model.save()
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
        model.file.save(FILENAME, open(file_path, 'rb'))


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
    model.file.save(FILENAME, open(file_path, 'rb'))
    assert not model.url
    assert model.file.name


@pytest.mark.django_db(transaction=True)
def test_checksumfile_file_yield_local_path(file_path):
    model = common.ChecksumFile()
    model.type = common.FileSourceType.FILE_FIELD
    model.file.save(FILENAME, open(file_path, 'rb'))
    model.save()
    with model.yield_local_path() as path:
        assert os.path.exists(path)
    if not HAS_FUSE:
        # Make sure it is cleaned up afer context ends
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
    if not HAS_FUSE:
        # Make sure it is cleaned up afer context ends
        assert not os.path.exists(path)
        # Now test that is gets cleaned up during an exception
        with pytest.raises(ValueError):
            with model.yield_local_path() as path:
                raise ValueError()
        assert not os.path.exists(path)


@pytest.mark.skipif(not HAS_FUSE, reason='simple_httpfs not installed.')
@pytest.mark.django_db(transaction=True)
def test_checksum_file_fuse_file_field(file_path):
    model = common.ChecksumFile()
    model.type = common.FileSourceType.FILE_FIELD
    model.file.save(FILENAME, open(file_path, 'rb'))
    model.save()
    assert precheck_fuse(model.get_url())
    with model.yield_local_path() as path:
        assert os.path.exists(path)
        assert str(path).startswith('/tmp/rgd/http')
        with open(path, 'r') as _:
            pass
