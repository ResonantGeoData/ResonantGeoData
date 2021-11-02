import os
import tempfile

import pytest
from rgd.datastore import datastore
from rgd.models import common, folder, utils

FILENAME = 'stars.png'


@pytest.fixture
def file_path():
    return datastore.fetch(FILENAME)


@pytest.mark.django_db(transaction=True)
def test_yield_local_path_file(file_path):
    model = common.ChecksumFile()
    model.type = common.FileSourceType.FILE_FIELD
    with open(file_path, 'rb') as f:
        model.file.save(FILENAME, f)
    model.folder = folder.Folder.objects.create()
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
def test_yield_checksumfiles(s3_url):
    # This tests downloading ChecksumFiles not in a Folder to the same directory
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
    with tempfile.TemporaryDirectory() as tempdir:
        with utils.yield_checksumfiles(files, tempdir) as directory:
            assert os.path.exists(directory)
            for f in files.all():
                assert os.path.exists(os.path.join(directory, f.name))


@pytest.mark.django_db(transaction=True)
def test_yield_checksumfiles_folder(s3_url):
    folder = common.Folder.objects.create()
    # Two URL files
    url = datastore.get_url('afie_1.jpg')
    file_1, _ = utils.get_or_create_checksumfile(url=url, name='afie_1.jpg', folder=folder)
    url = datastore.get_url('afie_2.jpg')
    file_2, _ = utils.get_or_create_checksumfile(
        url=url, name='the/best/dog/afie_2.jpeg', folder=folder
    )
    # One S3 URL file
    file_3, _ = utils.get_or_create_checksumfile(
        url=s3_url, name='s3/file/stuff.json', folder=folder
    )
    # One FileField file
    with open(datastore.fetch('afie_3.jpg'), 'rb') as f:
        file_4, _ = utils.get_or_create_checksumfile(file=f, name='afie_3.jpg', folder=folder)

    # Checkout all of these files under a single temporary directory through the folder
    # Note that 2 files are at top level and one file is nested
    files = common.ChecksumFile.objects.all()
    assert files.count() == 4
    with folder.yield_all_to_local_path() as directory:
        assert os.path.exists(directory)
        for f in files.all():
            assert os.path.exists(os.path.join(directory, f.name))
