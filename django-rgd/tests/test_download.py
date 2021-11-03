import os
import tempfile

import psutil
import pytest
from rgd import utility
from rgd.datastore import datastore
from rgd.models import ChecksumFile, FileSet, FileSourceType, utils

FILENAME = 'stars.png'


@pytest.fixture
def file_path():
    return datastore.fetch(FILENAME)


@pytest.mark.django_db(transaction=True)
def test_yield_local_path_file(file_path):
    model = ChecksumFile()
    model.type = FileSourceType.FILE_FIELD
    with open(file_path, 'rb') as f:
        model.file.save(FILENAME, f)
    model.file_set = FileSet.objects.create()
    model.save()
    path = model.yield_local_path()
    with model.yield_local_path() as path:
        assert os.path.exists(path)


@pytest.mark.django_db(transaction=True)
def test_yield_local_path_url_http():
    model = ChecksumFile()
    model.type = FileSourceType.URL
    model.url = datastore.get_url(FILENAME)
    model.save()
    with model.yield_local_path() as path:
        assert os.path.exists(path)


@pytest.mark.django_db(transaction=True)
def test_yield_local_path_url_s3(s3_url):
    model = ChecksumFile()
    model.type = FileSourceType.URL
    model.url = s3_url
    model.save()
    with model.yield_local_path() as path:
        assert os.path.exists(path)


@pytest.mark.django_db(transaction=True)
def test_yield_checksumfiles(s3_url):
    # This tests downloading ChecksumFiles not in a FileSet to the same directory
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
    files = ChecksumFile.objects.all()
    assert files.count() == 4
    with tempfile.TemporaryDirectory() as tempdir:
        with utils.yield_checksumfiles(files, tempdir) as directory:
            assert os.path.exists(directory)
            for f in files.all():
                assert os.path.exists(os.path.join(directory, f.name))


@pytest.mark.django_db(transaction=True)
def test_yield_checksumfiles_file_set(s3_url):
    file_set = FileSet.objects.create()
    # Two URL files
    url = datastore.get_url('afie_1.jpg')
    file_1, _ = utils.get_or_create_checksumfile(url=url, name='afie_1.jpg', file_set=file_set)
    url = datastore.get_url('afie_2.jpg')
    file_2, _ = utils.get_or_create_checksumfile(
        url=url, name='the/best/dog/afie_2.jpeg', file_set=file_set
    )
    # One S3 URL file
    file_3, _ = utils.get_or_create_checksumfile(
        url=s3_url, name='s3/file/stuff.json', file_set=file_set
    )
    # One FileField file
    with open(datastore.fetch('afie_3.jpg'), 'rb') as f:
        file_4, _ = utils.get_or_create_checksumfile(file=f, name='afie_3.jpg', file_set=file_set)

    # Checkout all of these files under a single temporary directory through the file_set
    # Note that 2 files are at top level and one file is nested
    files = ChecksumFile.objects.all()
    assert files.count() == 4
    with file_set.yield_all_to_local_path() as directory:
        assert os.path.exists(directory)
        for f in files.all():
            assert os.path.exists(os.path.join(directory, f.name))


@pytest.mark.django_db(transaction=True)
def test_clean_file_cache(checksum_file, checksum_file_url):
    f = FileSet.objects.create()
    checksum_file.file_set = f
    checksum_file.save(
        update_fields=[
            'file_set',
        ]
    )
    f.refresh_from_db()

    # Make sure clean_file_cache does not clean files in use
    with checksum_file_url.yield_local_path(yield_file_set=True) as path:
        assert os.path.exists(path)  # Make sure the file was checked out
        # Set target to size of drive to delete entire cache
        utility.clean_file_cache(override_target=psutil.disk_usage('/').total)
        assert os.path.exists(path)  # Make sure file is still present

    # Make sure the same works for `FileSet`s
    with f.yield_all_to_local_path() as directory:
        assert os.path.exists(directory)
        assert os.path.exists(checksum_file.get_cache_path())
        utility.clean_file_cache(override_target=psutil.disk_usage('/').total)
        assert os.path.exists(directory)
        assert os.path.exists(checksum_file.get_cache_path())
    # Checkout the file_set through a contained file
    with checksum_file.yield_local_path(yield_file_set=True) as path:
        assert os.path.exists(path)
        utility.clean_file_cache(override_target=psutil.disk_usage('/').total)
        assert os.path.exists(path)
