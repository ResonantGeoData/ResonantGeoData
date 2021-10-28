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


@pytest.fixture
def s3_url():
    return 's3://sentinel-cogs/sentinel-s2-l2a-cogs/2020/S2A_31QHU_20200714_0_L2A/S2A_31QHU_20200714_0_L2A.json'


@pytest.mark.django_db(transaction=True)
def test_create_local_file(file_path):
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
def test_create_url():
    model = common.ChecksumFile()
    model.type = common.FileSourceType.URL
    model.url = datastore.get_url(FILENAME)
    model.save()
    model.post_save_job()
    model.refresh_from_db()
    assert model.checksum == registry[FILENAME].split(':')[1]
    assert model.name


@pytest.mark.django_db(transaction=True)
def test_constraint_mismatch(file_path):
    with pytest.raises(IntegrityError):
        model = common.ChecksumFile()
        model.type = common.FileSourceType.FILE_FIELD
        model.url = datastore.get_url(FILENAME)
        model.save()
    with pytest.raises(IntegrityError):
        model = common.ChecksumFile()
        model.type = common.FileSourceType.URL
        with open(file_path, 'rb') as f:
            model.file.save(FILENAME, f)


@pytest.mark.django_db(transaction=True)
def test_constraint_url_null():
    with pytest.raises(IntegrityError):
        model = common.ChecksumFile()
        model.type = common.FileSourceType.URL
        model.save()


@pytest.mark.django_db(transaction=True)
def test_constraint_url_empty():
    with pytest.raises(IntegrityError):
        model = common.ChecksumFile()
        model.type = common.FileSourceType.URL
        model.url = ''  # empty string
        model.save()


@pytest.mark.django_db(transaction=True)
def test_constraint_file_with_empty_url(file_path):
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
def test_yield_local_path_file(file_path):
    model = common.ChecksumFile()
    model.type = common.FileSourceType.FILE_FIELD
    with open(file_path, 'rb') as f:
        model.file.save(FILENAME, f)
    model.save()
    path = model.yield_local_path()
    with model.yield_local_path() as path:
        assert os.path.exists(path)


@pytest.mark.django_db(transaction=True)
def test_yield_local_path_url_http():
    model = common.ChecksumFile()
    model.type = common.FileSourceType.URL
    model.url = datastore.get_url(FILENAME)
    model.save()
    with model.yield_local_path() as path:
        assert os.path.exists(path)


@pytest.mark.django_db(transaction=True)
def test_yield_local_path_url_s3(s3_url):
    model = common.ChecksumFile()
    model.type = common.FileSourceType.URL
    model.url = s3_url
    model.save()
    with model.yield_local_path() as path:
        assert os.path.exists(path)


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


@pytest.mark.django_db(transaction=True)
def test_yield_checksumfiles(s3_url):
    # Two URL files
    url = datastore.get_url('afie_1.jpg')
    file_1, _ = utils.get_or_create_checksumfile(url=url, name='afie_1.jpg')
    url = datastore.get_url('afie_2.jpg')
    file_2, _ = utils.get_or_create_checksumfile(url=url, name='the/best/dog/afie_2.jpeg')
    # One S3 URL file
    file_3, _ = utils.get_or_create_checksumfile(url=s3_url, name='s3/file/stuff.json')
    # One FileField file
    with open(datastore.fetch('afie_3.jpg'), 'rb') as f:
        file_4, _ = utils.get_or_create_checksumfile(file=f, name='afie_3.jpg')
    # Checkout all of these files under a single temporary directory
    # Note that 2 files are at top level and one file is nested
    files = common.ChecksumFile.objects.all()
    assert files.count() == 4
    with utils.yield_checksumfiles(files) as directory:
        assert os.path.exists(directory)
        for f in files.all():
            assert os.path.exists(os.path.join(directory, f.name))
    # Make sure the directory is cleaned up
    assert not os.path.exists(directory)
