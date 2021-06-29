from django.contrib.gis.db import models
from django.contrib.gis.geos import GEOSGeometry
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel
from rgd.models.mixins import PermissionPathMixin, TaskEventMixin
from rgd_imagery.tasks import jobs
from shapely.geometry import shape
from shapely.wkb import dumps

from .base import Image


class ProcessedImage(TimeStampedModel, TaskEventMixin, PermissionPathMixin):
    """Base class for processed images."""

    class Meta:
        abstract = True

    processed_image = models.ForeignKey(
        Image, on_delete=models.SET_NULL, null=True, related_name='+'
    )
    source_image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='+')

    def _post_delete(self, *args, **kwargs):
        # Cleanup the associated Image and ChecksumFile
        if self.processed_image:
            self.processed_image.file.delete()

    permissions_paths = ['source_image__file__collection__collection_permissions']


class ConvertedImage(ProcessedImage):
    """A model to store converted versions of an Image."""

    task_funcs = (jobs.task_convert_to_cog,)


class RegionImage(ProcessedImage):
    """A sub region of an Image."""

    task_funcs = (jobs.task_populate_region_image,)

    class SampleTypes(models.TextChoices):
        PIXEL_BOX = 'pixel box', _('Pixel bounding box')
        GEO_BOX = 'geographic box', _('Geographic bounding box')
        GEOJSON = 'geojson', _('GeoJSON feature')
        ANNOTATION = 'annotation', _('Annotation entry')

    sample_type = models.CharField(
        max_length=20, default=SampleTypes.PIXEL_BOX, choices=SampleTypes.choices
    )
    sample_parameters = models.JSONField()

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
            RegionImage.SampleTypes.PIXEL_BOX,
            RegionImage.SampleTypes.ANNOTATION,
        ):
            projection = 'pixels'

        if self.sample_type in (
            RegionImage.SampleTypes.GEO_BOX,
            RegionImage.SampleTypes.PIXEL_BOX,
        ):
            return p['left'], p['right'], p['bottom'], p['top'], projection
        elif self.sample_type == RegionImage.SampleTypes.GEOJSON:
            # Convert GeoJSON to extents
            geom = shape(p)
            feature = GEOSGeometry(memoryview(dumps(geom)))
            l, b, r, t = feature.extent  # (xmin, ymin, xmax, ymax)
            return l, r, b, t, projection
        elif self.sample_type == RegionImage.SampleTypes.ANNOTATION:
            from .annotation import Annotation

            ann_id = p['id']
            ann = Annotation.objects.get(id=ann_id)
            l, b, r, t = ann.segmentation.outline.extent  # (xmin, ymin, xmax, ymax)
            return l, r, b, t, projection
        else:
            raise ValueError('Sample type ({}) unknown.'.format(self.sample_type))
