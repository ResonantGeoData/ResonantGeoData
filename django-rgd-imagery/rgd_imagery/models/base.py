"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django.contrib.postgres.fields import DecimalRangeField
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.mixins import DetailViewMixin, PermissionPathMixin, TaskEventMixin
from rgd_imagery.tasks import jobs


class Image(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """This is a standalone DB entry for image files.

    This points to a single image file in an S3 file field.

    This will automatically generate an ``ImageMeta`` on the ``post_save``
    event. This points to data in its original location and the generated
    ``ImageMeta`` points to this.

    """

    permissions_paths = [('file', ChecksumFile)]
    task_funcs = (jobs.task_load_image,)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE, related_name='+')

    def image_data_link(self):
        return self.file.data_link()

    image_data_link.allow_tags = True


class ImageMeta(TimeStampedModel, PermissionPathMixin):
    """Single image entry, tracks the original file."""

    permissions_paths = [('parent_image', Image)]

    parent_image = models.OneToOneField(Image, on_delete=models.CASCADE)
    driver = models.CharField(max_length=100)
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    number_of_bands = (
        models.PositiveIntegerField()
    )  # TODO: code smell? this can be computed relationally


class BandMeta(TimeStampedModel, PermissionPathMixin):
    """A basic container to keep track of useful band info."""

    permissions_paths = [('parent_image', Image)]
    parent_image = models.ForeignKey(Image, on_delete=models.CASCADE)
    band_number = models.IntegerField()
    description = models.TextField(
        null=True,
        blank=True,
        help_text='Automatically retrieved from raster but can be overwritten.',
    )
    max = models.FloatField(null=True)
    min = models.FloatField(null=True)
    mean = models.FloatField(null=True)
    std = models.FloatField(null=True)
    nodata_value = models.FloatField(null=True)
    interpretation = models.TextField()
    band_range = DecimalRangeField(
        null=True, help_text='The spectral range of the band (in micrometers).'
    )


class ImageSet(TimeStampedModel, PermissionPathMixin):
    """Container for many images."""

    permissions_paths = [('images', Image)]

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    images = models.ManyToManyField(Image)

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

    permissions_paths = [('image_set', ImageSet)]
    detail_view_name = 'image-set-spatial-detail'

    image_set = models.OneToOneField(ImageSet, on_delete=models.CASCADE)

    @property
    def name(self):
        return self.image_set.name
