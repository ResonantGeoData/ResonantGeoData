"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.mixins import DetailViewMixin, PermissionPathMixin, TaskEventMixin
from rgd_imagery.tasks import jobs


class ImageFile(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """This is a standalone DB entry for image files.

    This points to a single image file in an S3 file field.

    This will automatically generate an ``ImageEntry`` on the ``post_save``
    event. This points to data in its original location and the generated
    ``ImageEntry`` points to this.

    """

    permissions_paths = ['file__collection__collection_permissions']
    task_funcs = (jobs.task_read_image_file,)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE)

    def image_data_link(self):
        return self.file.data_link()

    image_data_link.allow_tags = True


class ImageEntry(TimeStampedModel, PermissionPathMixin):
    """Single image entry, tracks the original file."""

    permissions_paths = ['image_file__file__collection__collection_permissions']

    def __str__(self):
        return f'{self.name} ({self.id})'

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    image_file = models.OneToOneField(ImageFile, on_delete=models.CASCADE)
    driver = models.CharField(max_length=100)
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    number_of_bands = models.PositiveIntegerField()


class BandMetaEntry(TimeStampedModel, PermissionPathMixin):
    """A basic container to keep track of useful band info."""

    permissions_paths = ['parent_image__image_file__file__collection__collection_permissions']
    parent_image = models.ForeignKey(ImageEntry, on_delete=models.CASCADE)
    band_number = models.IntegerField()
    description = models.TextField(
        null=True,
        blank=True,
        help_text='Automatically retreived from raster but can be overwritten.',
    )
    dtype = models.CharField(max_length=10)
    max = models.FloatField(null=True)
    min = models.FloatField(null=True)
    mean = models.FloatField(null=True)
    std = models.FloatField(null=True)
    nodata_value = models.FloatField(null=True)
    interpretation = models.TextField()


class ImageSet(TimeStampedModel, PermissionPathMixin):
    """Container for many images."""

    permissions_paths = ['images__image_file__file__collection__collection_permissions']

    def __str__(self):
        return f'{self.name} ({self.id} - {type(self)}'

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    images = models.ManyToManyField(ImageEntry)

    @property
    def image_bands(self):
        return self.images.aggregate(models.Sum('number_of_bands'))['number_of_bands__sum']

    @property
    def width(self):
        return self.images.aggregate(models.Max('width'))['width__max']

    @property
    def height(self):
        return self.images.aggregate(models.Max('height'))['height__max']

    @property
    def count(self):
        return self.images.count()

    def get_all_annotations(self):
        annots = {}
        for image in self.images.all():
            annots[image.pk] = image.annotation_set.all()
        return annots


class ImageSetSpatial(TimeStampedModel, SpatialEntry, PermissionPathMixin, DetailViewMixin):
    """Arbitrary register an ImageSet to a location."""

    permissions_paths = ['image_set__images__image_file__file__collection__collection_permissions']
    detail_view_name = 'image-set-spatial-detail'

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    image_set = models.OneToOneField(ImageSet, on_delete=models.CASCADE)
