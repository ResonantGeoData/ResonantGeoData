from django.db import IntegrityError
import pytest
from rgd.datastore import datastore, registry
from rgd.models import ChecksumFile, FileSourceType, utils
from rgd.models.collection import Collection

FILENAME = 'stars.png'


@pytest.fixture
def file_path():
    return datastore.fetch(FILENAME)


@pytest.mark.django_db(transaction=True)
def test_create_local_file(file_path):
    model = ChecksumFile()
    model.type = FileSourceType.FILE_FIELD
    with open(file_path, 'rb') as f:
        model.file.save(FILENAME, f)
    model.save()
    model.post_save_job()
    model.refresh_from_db()
    assert model.checksum == registry[FILENAME].split(':')[1]
    assert model.name == FILENAME


@pytest.mark.django_db(transaction=True)
def test_create_url():
    model = ChecksumFile()
    model.type = FileSourceType.URL
    model.url = datastore.get_url(FILENAME)
    model.save()
    model.post_save_job()
    model.refresh_from_db()
    assert model.checksum == registry[FILENAME].split(':')[1]
    assert model.name


@pytest.mark.django_db(transaction=True)
def test_constraint_mismatch(file_path):
    with pytest.raises(IntegrityError):
        model = ChecksumFile()
        model.type = FileSourceType.FILE_FIELD
        model.url = datastore.get_url(FILENAME)
        model.save()
    with pytest.raises(IntegrityError):
        model = ChecksumFile()
        model.type = FileSourceType.URL
        with open(file_path, 'rb') as f:
            model.file.save(FILENAME, f)


@pytest.mark.django_db(transaction=True)
def test_constraint_url_null():
    with pytest.raises(IntegrityError):
        model = ChecksumFile()
        model.type = FileSourceType.URL
        model.save()


@pytest.mark.django_db(transaction=True)
def test_constraint_url_empty():
    with pytest.raises(IntegrityError):
        model = ChecksumFile()
        model.type = FileSourceType.URL
        model.url = ''  # empty string
        model.save()


@pytest.mark.django_db(transaction=True)
def test_constraint_file_with_empty_url(file_path):
    # Make sure the constraint passes when an empty string URL is given with
    #   the FileField choice. This happens when adding files in the admin interface
    model = ChecksumFile()
    model.type = FileSourceType.FILE_FIELD
    model.url = ''
    with open(file_path, 'rb') as f:
        model.file.save(FILENAME, f)
    assert not model.url
    assert model.file.name


@pytest.mark.django_db(transaction=True)
def test_get_or_create_file(file_path):
    with open(file_path, 'rb') as f:
        file, created = utils.get_or_create_checksumfile(file=f)
    assert created
    with open(file_path, 'rb') as f:
        file, created = utils.get_or_create_checksumfile(file=f)
    assert not created


@pytest.mark.django_db(transaction=True)
def test_get_or_create_file_permissions(file_path):
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
def test_get_or_create_url():
    url = datastore.get_url(FILENAME)
    file, created = utils.get_or_create_checksumfile(url=url)
    assert created
    file, created = utils.get_or_create_checksumfile(url=url)
    assert not created


@pytest.mark.django_db(transaction=True)
def test_get_or_create_url_permissions():
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
def test_get_or_create_url_checksum():
    url = datastore.get_url(FILENAME)
    file, created = utils.get_or_create_checksumfile(url=url)
    assert created
    file, created = utils.get_or_create_checksumfile(url=url, precompute_url_checksum=True)
    assert not created
