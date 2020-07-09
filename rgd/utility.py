from contextlib import contextmanager
import hashlib
from pathlib import Path, PurePath
import shutil
import tempfile
from typing import Generator

from django.core.files import File
from django.db.models.fields.files import FieldFile
from storages.backends.s3boto3 import S3Boto3StorageFile


@contextmanager
def _field_file_to_local_path(field_file: FieldFile) -> Generator[Path, None, None]:
    with field_file.open('rb'):
        file_obj: File = field_file.file

        if not Path(file_obj.name).exists() or isinstance(file_obj, S3Boto3StorageFile):
            field_file_basename = PurePath(field_file.name).name
            with tempfile.NamedTemporaryFile('wb', suffix=field_file_basename) as dest_stream:
                shutil.copyfileobj(file_obj, dest_stream)
                dest_stream.flush()

                yield Path(dest_stream.name)
        else:
            yield Path(file_obj.name)


def compute_checksum(file_path, chunk_num_blocks=128):
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_num_blocks * sha256.block_size):
            sha256.update(chunk)
    return sha256.hexdigest()
