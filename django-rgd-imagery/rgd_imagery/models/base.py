"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django.contrib.postgres.fields import DecimalRangeField
from django_extensions.db.models import TimeStampedModel
from rgd.models import ChecksumFile, SpatialEntry
from rgd.models.mixins import DetailViewMixin, TaskEventMixin
from rgd_imagery.tasks import jobs


class Image(TimeStampedModel, TaskEventMixin):
    """This is a standalone DB entry for image files.

    This points to a single image file in an S3 file field.

    This will automatically generate an ``ImageMeta`` on the ``post_save``
    event. This points to data in its original location and the generated
    ``ImageMeta`` points to this.

    """

    task_funcs = (jobs.task_load_image,)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE, related_name='+')

    def image_data_link(self):
        return self.file.data_link()

    image_data_link.allow_tags = True

    @property
    def number_of_bands(self):
        return self.bandmeta_set.count()

    def get_processed_images(self, images=None):
        if images is None:
            images = set()
        for proc in self.processedimage_set.exclude(processed_image__in=images):
            if proc.processed_image:
                images.add(proc.processed_image)
                images.update(proc.processed_image.get_processed_images(images))
        return images

    @property
    def processed_images(self):
        return self.get_processed_images(self)


class ImageMeta(TimeStampedModel):
    """Single image entry, tracks the original file."""

    parent_image = models.OneToOneField(Image, on_delete=models.CASCADE)
    driver = models.CharField(max_length=100)
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()


class BandMeta(TimeStampedModel):
    """A basic container to keep track of useful band info."""

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


class ImageSet(TimeStampedModel):
    """Container for many images."""

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    images = models.ManyToManyField(Image)

    @property
    def number_of_bands(self):
        return sum([im.number_of_bands for im in self.images.all()])

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

    @property
    def processed_images(self):
        images = set()
        for image in self.images.all():
            images.update(image.get_processed_images(images))
        pks = [im.pk for im in images]
        return Image.objects.filter(pk__in=pks).order_by('pk')

    @property
    def all_images(self):
        images = set()
        for image in self.images.all():
            images.add(image)
            images.update(image.get_processed_images(images))
        pks = [im.pk for im in images]
        return Image.objects.filter(pk__in=pks).order_by('pk')

    detail_view_name = 'image-set-detail'


class ImageSetSpatial(TimeStampedModel, SpatialEntry, DetailViewMixin):
    """Arbitrary register an ImageSet to a location."""

    detail_view_name = 'image-set-detail'
    detail_view_pk = 'image_set__pk'

    image_set = models.OneToOneField(ImageSet, on_delete=models.CASCADE)

    @property
    def name(self):
        return self.image_set.name
