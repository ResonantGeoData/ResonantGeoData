"""Base classes for raster dataset entries."""
from django.contrib.gis.db import models
from django.contrib.postgres import fields
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from ... import tasks
from ..common import ChecksumFile, SpatialEntry
from ..mixins import TaskEventMixin


class ImageFile(TimeStampedModel, TaskEventMixin):
    """This is a standalone DB entry for image files.

    This points to a single image file in an S3 file field.

    This will automatically generate an ``ImageEntry`` on the ``post_save``
    event. This points to data in its original location and the generated
    ``ImageEntry`` points to this.

    """

    task_funcs = (tasks.task_read_image_file,)
    file = models.ForeignKey(ChecksumFile, on_delete=models.CASCADE)

    def image_data_link(self):
        return self.file.data_link()

    image_data_link.allow_tags = True


class ImageEntry(TimeStampedModel):
    """Single image entry, tracks the original file."""

    def __str__(self):
        return f'{self.name} ({self.id})'

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    instrumentation = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text='The instrumentation used to acquire these data.',
    )

    image_file = models.OneToOneField(ImageFile, on_delete=models.CASCADE)
    driver = models.CharField(max_length=100)
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()
    number_of_bands = models.PositiveIntegerField()


class ImageSet(TimeStampedModel):
    """Container for many images."""

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


class RasterEntry(TimeStampedModel, TaskEventMixin):
    """This class is a container for the metadata of a raster.

    This model inherits from ``ImageSet`` and only adds an extra layer of
    geospatial context to the ``ImageSet``.

    """

    def __str__(self):
        return 'ID: {} {} (type: {})'.format(self.id, self.name, type(self))

    name = models.CharField(max_length=1000, blank=True)
    description = models.TextField(null=True, blank=True)

    image_set = models.OneToOneField(ImageSet, on_delete=models.CASCADE)

    task_funcs = (
        tasks.task_populate_raster_entry,
        # tasks.task_populate_raster_footprint,
    )

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


class RasterMetaEntry(TimeStampedModel, SpatialEntry):

    parent_raster = models.OneToOneField(RasterEntry, on_delete=models.CASCADE)

    # Raster fields
    crs = models.TextField(help_text='PROJ string')  # PROJ String
    origin = fields.ArrayField(models.FloatField(), size=2)
    extent = fields.ArrayField(models.FloatField(), size=4)
    resolution = fields.ArrayField(models.FloatField(), size=2)  # AKA scale
    # TODO: skew/transform
    transform = fields.ArrayField(models.FloatField(), size=6)

    @property
    def name(self):
        return self.parent_raster.name


class BandMetaEntry(TimeStampedModel):
    """A basic container to keep track of useful band info."""

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


class ConvertedImageFile(TimeStampedModel, TaskEventMixin):
    """A model to store converted versions of a raster entry."""

    task_funcs = (tasks.task_convert_to_cog,)
    converted_file = models.OneToOneField(ChecksumFile, on_delete=models.SET_NULL, null=True)
    source_image = models.OneToOneField(ImageEntry, on_delete=models.CASCADE)

    def _post_delete(self, *args, **kwargs):
        # Cleanup the associated ChecksumFile
        self.converted_file.delete()


class SubsampledImage(TimeStampedModel, TaskEventMixin):
    """A subsample of an ImageEntry."""

    task_funcs = (tasks.task_populate_subsampled_image,)

    class SampleTypes(models.TextChoices):
        PIXEL_BOX = 'pixel box', _('Pixel bounding box')
        GEO_BOX = 'geographic box', _('Geographic bounding box')
        GEOJSON = 'geojson', _('GeoJSON feature')
        ANNOTATION = 'annotation', _('Annotation entry')

    source_image = models.ForeignKey(ImageEntry, on_delete=models.CASCADE)
    sample_type = models.CharField(
        max_length=20, default=SampleTypes.PIXEL_BOX, choices=SampleTypes.choices
    )
    sample_parameters = models.JSONField()

    data = models.OneToOneField(ChecksumFile, on_delete=models.SET_NULL, null=True)

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
        elif self.sample_type == SubsampledImage.SampleTypes.ANNOTATION:
            from .annotation import Annotation

            ann_id = p['id']
            outline = p.get('outline', False)
            ann = Annotation.objects.get(id=ann_id)
            return ann.segmentation.get_subsample_args(outline=outline)
        else:
            raise ValueError('Sample type ({}) unknown.'.format(self.sample_type))

    def _post_delete(self, *args, **kwargs):
        # Cleanup the associated ChecksumFile
        self.data.delete()


class KWCOCOArchive(TimeStampedModel, TaskEventMixin):
    """A container for holding imported KWCOCO datasets.

    User must upload a JSON file of the KWCOCO meta info and an optional
    archive of images - optional because images can come from URLs instead of
    files.

    """

    task_funcs = (tasks.task_load_kwcoco_dataset,)
    name = models.CharField(max_length=1000, blank=True)
    spec_file = models.OneToOneField(
        ChecksumFile,
        on_delete=models.CASCADE,
        related_name='kwcoco_spec_file',
        help_text='The JSON spec file.',
    )
    image_archive = models.OneToOneField(
        ChecksumFile,
        null=True,
        on_delete=models.CASCADE,
        related_name='kwcoco_image_archive',
        help_text='An archive (.tar or .zip) of the images referenced by the spec file (optional).',
    )
    # Allowed null because model must be saved before task can populate this
    image_set = models.OneToOneField(ImageSet, on_delete=models.SET_NULL, null=True)

    def _post_delete(self, *args, **kwargs):
        # Frist delete all the images in the image set
        #  this will cascade to the annotations
        images = self.image_set.images.all()
        for image in images:
            # This should cascade to the ImageFile and the ImageEntry
            image.image_file.file.delete()
        # Now delete the empty image set
        self.image_set.delete()
