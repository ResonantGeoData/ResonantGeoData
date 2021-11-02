from django_extensions.db.models import TimeStampedModel
from rgd.utility import get_cache_dir


class Folder(TimeStampedModel):
    @property
    def files(self):
        return self.checksumfile_set.all()

    def get_cache_path(self):
        """Generate a predetermined path in the cache directory.

        This makes a directory under the cache directory for each ChecksumFile
        record. The subdirectory is the Primary Key of the record and the nested
        files are the file itself, lockfile, and any additional files used or
        generated by third party libraries.

        `<cache directory>/<pk>/*`

        """
        p = get_cache_dir() / f'{self.pk}'
        p.mkdir(exist_ok=True, parents=True)
        return p

    def yield_all_to_local_path(self, directory: str = None):
        """Download all the files in this folder to a local path.

        Please note that this uses a contextmanager to acquire a lock on the
        directory to make sure the files are not automatically cleaned up by
        other threads or processes.

        """
        from .utils import yield_checksumfiles  # avoiding circular import

        if not directory:
            directory = self.get_cache_path()
        return yield_checksumfiles(self.files, directory)
