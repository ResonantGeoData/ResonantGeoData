import os

from django.db import IntegrityError
import pytest
from rgd.datastore import datastore, registry
from rgd.models import common, utils
from rgd.models.collection import Collection

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


@pytest.mark.django_db(transaction=True)
def test_get_or_create_checksumfile_file(file_path):
    with open(file_path, 'rb') as f:
        file, created = utils.get_or_create_checksumfile(file=f)
    assert created
    with open(file_path, 'rb') as f:
        file, created = utils.get_or_create_checksumfile(file=f)
    assert not created


@pytest.mark.django_db(transaction=True)
def test_get_or_create_checksumfile_file_permissions(file_path):
    collection = Collection.objects.create(name='Foo')
    with open(file_path, 'rb') as f:
        file, created = utils.get_or_create_checksumfile(collection=collection, file=f)
    assert created
    assert file.collection == collection
    with open(file_path, 'rb') as f:
        file, created = utils.get_or_create_checksumfile(collection=collection, file=f)
    assert not created
    with open(file_path, 'rb') as f:
        file, created = utils.get_or_create_checksumfile(file=f)
    # Because this passed collection is None, make sure a new file is created
    assert created
    assert file.collection is None


@pytest.mark.django_db(transaction=True)
def test_get_or_create_checksumfile_url():
    url = datastore.get_url(FILENAME)
    file, created = utils.get_or_create_checksumfile(url=url)
    assert created
    file, created = utils.get_or_create_checksumfile(url=url)
    assert not created


@pytest.mark.django_db(transaction=True)
def test_get_or_create_checksumfile_url_permissions():
    url = datastore.get_url(FILENAME)
    collection = Collection.objects.create(name='Foo')
    file, created = utils.get_or_create_checksumfile(collection=collection, url=url)
    assert created
    assert file.collection == collection
    file, created = utils.get_or_create_checksumfile(collection=collection, url=url)
    assert not created
    # Because this passed collection is None, make sure a new file is created
    file, created = utils.get_or_create_checksumfile(url=url)
    assert created
    assert file.collection is None


@pytest.mark.django_db(transaction=True)
def test_yield_checksumfiles():
    # Two URL files
    url = datastore.get_url('afie_1.jpg')
    file_1, _ = utils.get_or_create_checksumfile(url=url, name='afie_1.jpg')
    url = datastore.get_url('afie_2.jpg')
    file_2, _ = utils.get_or_create_checksumfile(url=url, name='the/best/dog/afie_2.jpeg')
    # One FileField file
    with open(datastore.fetch('afie_3.jpg'), 'rb') as f:
        file_3, _ = utils.get_or_create_checksumfile(file=f, name='afie_3.jpg')
    # Checkout all of these files under a single temporary directory
    # Note that 2 files are at top level and one file is nested
    files = common.ChecksumFile.objects.all()
    with utils.yield_checksumfiles(files) as directory:
        assert os.path.exists(directory)
        for f in files.all():
            assert os.path.exists(os.path.join(directory, f.name))
