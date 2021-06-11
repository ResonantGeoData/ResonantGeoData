from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.utils.translation import gettext_lazy as _
from rgd.models import ChecksumFile, ModifiableEntry
from rgd.models.mixins import TaskEventMixin
from rgd_imagery.tasks import jobs
from shapely.geometry import shape
from shapely.wkb import dumps

from .base import ImageEntry


class ConvertedImageFile(ModifiableEntry, TaskEventMixin):
    """A model to store converted versions of a raster entry."""

    task_funcs = (jobs.task_convert_to_cog,)
    converted_file = models.OneToOneField(ChecksumFile, on_delete=models.SET_NULL, null=True)
    source_image = models.OneToOneField(ImageEntry, on_delete=models.CASCADE)

    def _post_delete(self, *args, **kwargs):
        # Cleanup the associated ChecksumFile
        if self.converted_file:
            self.converted_file.delete()


class SubsampledImage(ModifiableEntry, TaskEventMixin):
    """A subsample of an ImageEntry."""

    task_funcs = (jobs.task_populate_subsampled_image,)

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

    def get_extent(self):
        """Convert ``sample_parameters`` to length 4 tuple of XY extents.

        Note
        ----
        A ``KeyError`` could be raised if the sample parameters are illformed.

        Return
        ------
        extents, projection: <left, right, bottom, top>, <projection>

        """
        p = self.sample_parameters

        projection = p.pop('projection', None)
        if self.sample_type in (
            SubsampledImage.SampleTypes.PIXEL_BOX,
            SubsampledImage.SampleTypes.ANNOTATION,
        ):
            projection = 'pixels'

        if self.sample_type in (
            SubsampledImage.SampleTypes.GEO_BOX,
            SubsampledImage.SampleTypes.PIXEL_BOX,
        ):
            return p['left'], p['right'], p['bottom'], p['top'], projection
        elif self.sample_type == SubsampledImage.SampleTypes.GEOJSON:
            # Convert GeoJSON to extents
            geom = shape(p)
            feature = GEOSGeometry(memoryview(dumps(geom)))
            l, b, r, t = feature.extent  # (xmin, ymin, xmax, ymax)
            return l, r, b, t, projection
        elif self.sample_type == SubsampledImage.SampleTypes.ANNOTATION:
            from .annotation import Annotation

            ann_id = p['id']
            ann = Annotation.objects.get(id=ann_id)
            l, b, r, t = ann.segmentation.outline.extent  # (xmin, ymin, xmax, ymax)
            return l, r, b, t, projection
        else:
            raise ValueError('Sample type ({}) unknown.'.format(self.sample_type))

    def _post_delete(self, *args, **kwargs):
        # Cleanup the associated ChecksumFile
        self.data.delete()
