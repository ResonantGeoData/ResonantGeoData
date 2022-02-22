import logging
import os
from pathlib import Path

from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, FileSet, SpatialEntry
from rgd.models.mixins import DetailViewMixin, TaskEventMixin
from rgd.models.utils import get_or_create_checksumfile_file_field
from rgd_3d.tasks import jobs

logger = logging.getLogger(__name__)


class Tiles3D(TimeStampedModel, TaskEventMixin, DetailViewMixin):
    class Meta:
        verbose_name = '3D tiles'
        verbose_name_plural = '3D tiles'

    def clean(self):
        if self.json_file.file_set is None:
            raise ValidationError('"json_file" must be part of a FileSet.')
        return super().clean()

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    json_file = models.ForeignKey(
        ChecksumFile,
        on_delete=models.CASCADE,
        related_name='+',
        help_text='The `tileset.json` file that contains metadata about this set of 3D tiles.',
    )

    task_funcs = (jobs.task_read_3d_tiles_file,)
    detail_view_name = 'detail-tiles-3d'


class Tiles3DMeta(TimeStampedModel, SpatialEntry):
    source = models.OneToOneField(Tiles3D, on_delete=models.CASCADE)

    @property
    def name(self):
        return self.source.json_file.name

    detail_view_name = Tiles3D.detail_view_name
    detail_view_pk = 'source__pk'


def create_tiles3d_from_paths(paths, collection=None):
    # Start by ingesting tileset.json
    # tileset_json_path.resolve().parent
    tileset_json_path = Path([path for path in paths if path.split('/')[-1] == 'tileset.json'][0])
    tileset_json_name = '/'.join(str(tileset_json_path).split('/')[-2:])

    logger.error(tileset_json_path)

    dataset_name = os.path.basename(tileset_json_path.parent)

    # Create a FileSet for the 3D tiles dataset
    fileset, created = FileSet.objects.get_or_create(name=dataset_name)

    with open(tileset_json_path, 'rb') as f:
        tileset_json_checksum_file, _ = get_or_create_checksumfile_file_field(
            f, collection=collection
        )
    tileset_json_checksum_file.file_set = fileset
    tileset_json_checksum_file.name = tileset_json_name
    tileset_json_checksum_file.save(update_fields=['file_set', 'name'])

    # Filter out tileset.json as we have already ingested that
    paths = [path for path in paths if path.split('/')[-1] != 'tileset.json']

    for path in paths:
        try:
            Path(path).relative_to(tileset_json_path.parent)
        except ValueError:
            continue
        # Strip off irrelevant parts of file path
        logger.error(path)
        file_name = Path(path).relative_to(tileset_json_path.parent.parent)
        logger.error(file_name)
        with open(path, 'rb') as f:
            checksum_file, _ = get_or_create_checksumfile_file_field(f, collection=collection)
        checksum_file.file_set = fileset
        checksum_file.name = file_name
        checksum_file.save(update_fields=['file_set', 'name'])

    entry, created = Tiles3D.objects.get_or_create(
        name=dataset_name, json_file=tileset_json_checksum_file
    )
    return entry
