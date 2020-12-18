"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django.contrib.postgres import fields
from django.utils.html import escape, mark_safe
from django.utils.translation import gettext_lazy as _

from ... import tasks
from ..common import ArbitraryFile, ModifiableEntry, SpatialEntry
from ..mixins import Status, TaskEventMixin
from .ifiles import BaseImageFile


class ImageEntry(ModifiableEntry):
    """Single image entry, tracks the original file."""

    def __str__(self):
        return f'{self.name} ({self.id})'

    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(null=True, blank=True)

    instrumentation = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='The instrumentation used to acquire these data.',
    )

    image_file = models.OneToOneField(BaseImageFile, on_delete=models.CASCADE)
    driver = models.CharField(max_length=100)
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    number_of_bands = models.PositiveIntegerField()
    metadata = models.JSONField(null=True)


class Thumbnail(ModifiableEntry):
    """Thumbnail model and utility for ImageEntry."""

    image_entry = models.OneToOneField(ImageEntry, on_delete=models.CASCADE)

    base_thumbnail = models.ImageField(upload_to='thumbnails')

    def image_tag(self):
        return mark_safe(
            u'<img src="%s" id="thumbnail" width="500"/>' % escape(self.base_thumbnail.url)
        )

    image_tag.short_description = 'Image'
    image_tag.allow_tags = True


class ImageSet(ModifiableEntry):
    """Container for many images."""

    def __str__(self):
        return f'{self.name} ({self.id} - {type(self)}'

    name = models.CharField(max_length=100, blank=True)
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


class RasterEntry(ModifiableEntry, TaskEventMixin):
    """This class is a container for the metadata of a raster.

    This model inherits from ``ImageSet`` and only adds an extra layer of
    geospatial context to the ``ImageSet``.

    """

    def __str__(self):
        return 'ID: {} {} (type: {})'.format(self.id, self.name, type(self))

    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(null=True, blank=True)

    image_set = models.OneToOneField(ImageSet, on_delete=models.CASCADE)

    task_func = tasks.task_populate_raster_entry
    failure_reason = models.TextField(null=True)
    status = models.CharField(max_length=20, default=Status.CREATED, choices=Status.choices)

    @property
    def footprint(self):
        """Pointer to RasterMetaEntry footprint."""
        return self.rastermetaentry.footprint

    @property
    def outline(self):
        """Pointer to RasterMetaEntry outline."""
        return self.rastermetaentry.outline

    @property
    def count(self):
        """Get number of bands across all images in image set."""
        n = 0
        for im in self.image_set.images.all():
            n += im.number_of_bands
        return n


class RasterMetaEntry(ModifiableEntry, SpatialEntry):

    parent_raster = models.OneToOneField(RasterEntry, on_delete=models.CASCADE)

    # Raster fields
    crs = models.TextField(help_text='PROJ string')  # PROJ String
    origin = fields.ArrayField(models.FloatField(), size=2)
    extent = fields.ArrayField(models.FloatField(), size=4)
    resolution = fields.ArrayField(models.FloatField(), size=2)  # AKA scale
    # TODO: skew/transform
    transform = fields.ArrayField(models.FloatField(), size=6)


class BandMetaEntry(ModifiableEntry):
    """A basic container to keep track of useful band info."""

    parent_image = models.ForeignKey(ImageEntry, on_delete=models.CASCADE)
    band_number = models.IntegerField()
    description = models.TextField(
        null=True,
        blank=True,
        help_text='Automatically retreived from raster but can be overwritten.',
    )
    dtype = models.CharField(max_length=10)
    max = models.FloatField()
    min = models.FloatField()
    mean = models.FloatField()
    std = models.FloatField()
    nodata_value = models.FloatField(null=True)
    interpretation = models.TextField()


class ConvertedImageFile(ModifiableEntry, TaskEventMixin):
    """A model to store converted versions of a raster entry."""

    task_func = tasks.task_convert_to_cog
    converted_file = models.OneToOneField(ArbitraryFile, on_delete=models.CASCADE, null=True)
    failure_reason = models.TextField(null=True)
    status = models.CharField(max_length=20, default=Status.CREATED, choices=Status.choices)
    source_image = models.OneToOneField(ImageEntry, on_delete=models.CASCADE)


class SubsampledImage(ModifiableEntry, TaskEventMixin):
    """A subsample of an ImageEntry."""

    task_func = tasks.task_populate_subsampled_image

    class SampleTypes(models.TextChoices):
        PIXEL_BOX = 'pixel box', _('Pixel bounding box')
        GEO_BOX = 'geographic box', _('Geographic bounding box')
        GEOJSON = 'geojson', _('GeoJSON feature')

    source_image = models.ForeignKey(ImageEntry, on_delete=models.CASCADE)
    sample_type = models.CharField(
        max_length=20, default=SampleTypes.PIXEL_BOX, choices=SampleTypes.choices
    )
    sample_parameters = models.JSONField()

    data = models.OneToOneField(ArbitraryFile, on_delete=models.CASCADE, null=True)

    failure_reason = models.TextField(null=True)
    status = models.CharField(max_length=20, default=Status.CREATED, choices=Status.choices)

    def to_kwargs(self):
        """Convert ``sample_parameters`` to kwargs ready for GDAL.

        Note
        ----
        A ``KeyError`` could be raised if the sample parameters are illformed.

        """
        p = self.sample_parameters
        if self.sample_type == SubsampledImage.SampleTypes.PIXEL_BOX:
            # -srcwin <xoff> <yoff> <xsize> <ysize>
            return dict(srcWin=[p['umin'], p['vmin'], p['umax'] - p['umin'], p['vmax'] - p['vmin']])
        elif self.sample_type == SubsampledImage.SampleTypes.GEO_BOX:
            # -projwin ulx uly lrx lry
            return dict(projWin=[p['xmin'], p['ymax'], p['xmax'], p['ymin']])
        elif self.sample_type == SubsampledImage.SampleTypes.GEOJSON:
            return p
        else:
            raise ValueError('Sample type ({}) unknown.'.format(self.sample_type))


class KWCOCOArchive(ModifiableEntry, TaskEventMixin):
    """A container for holding imported KWCOCO datasets.

    User must upload a JSON file of the KWCOCO meta info and an optional
    archive of images - optional because images can come from URLs instead of
    files.

    """

    task_func = tasks.task_load_kwcoco_dataset
    name = models.CharField(max_length=100, blank=True)
    failure_reason = models.TextField(null=True)
    status = models.CharField(max_length=20, default=Status.CREATED, choices=Status.choices)
    spec_file = models.OneToOneField(
        ArbitraryFile,
        on_delete=models.CASCADE,
        related_name='kwcoco_spec_file',
        help_text='The JSON spec file.',
    )
    image_archive = models.OneToOneField(
        ArbitraryFile,
        null=True,
        on_delete=models.CASCADE,
        related_name='kwcoco_image_archive',
        help_text='An archive (.tar or .zip) of the images referenced by the spec file (optional).',
    )
    # Allowed null because model must be saved before task can populate this
    image_set = models.OneToOneField(ImageSet, on_delete=models.DO_NOTHING, null=True)

    def _post_delete(self, *args, **kwargs):
        # Frist delete all the images in the image set
        #  this will cascade to the annotations
        images = self.image_set.images.all()
        for image in images:
            image.image_file.delete()
        # Now delete the empty image set
        self.image_set.delete()
