from itertools import groupby

from django.contrib.gis.db import models
from django.contrib.gis.gdal import GDALRaster
import numpy as np

from .base import ImageEntry
from ..common import ModifiableEntry


class Segmentation(models.Model):
    """A base class for segmentations as there are different kinds.

    There two types of segmentations:

    * polygon: one/many shape(s) in pixel coordinates (can be decimal)
    * run-length-encoded (RLE): a bit mask of the entire image to label one thing (or a crowd of that thing)

    Note
    ----
    All geometry in pixel space of the parent Annotation's image (note the SRID
    of 0 for all geometry fields).

    The segmentation is stored in child class as the ``feature`` attribute.

    """

    # COCO bounding box format is [top left x position, top left y position, width, height]
    # This should come from the COCO format rather than be autopopulated by us
    outline = models.PolygonField(srid=0, null=True, help_text='The bounding box')


class PolygonSegmentation(Segmentation):
    """one/many shape(s) in pixel coordinates (can be decimal).

    Note
    ----
    We use ``MultiPolygonField`` as the segmentation can be multiple
    seperated polygons across the image.

    """

    feature = models.MultiPolygonField(srid=0, null=True)


class RLESegmentation(Segmentation):
    """run-length-encoded (RLE) segmentation.

    A bit mask of the entire image to label one thing (or a crowd of that
    thing). We will treat this as a raster overlain the image.

    """

    feature = models.RasterField(srid=0, null=True)

    def _from_rle(self, rle):
        """Populate the feature ``RasterField`` from an RLE array.

        Parameters
        ----------
        rle : dict
            A dictionary with ``counts`` and ``size`` fields
        """
        counts = rle['counts']
        width, height = rle['size']
        mask = np.zeros((width, height), dtype=np.uint8).ravel()
        current = 0
        flag = False
        for count in counts:
            mask[current : current + count] = flag
            current += count
            flag = not flag
        rst = GDALRaster(
            {
                'width': width,
                'height': height,
                'srid': 0,
                'origin': [0, 0],
                'bands': [{'data': mask, 'nodata_value': 0}],
            }
        )
        self.feature = rst
        return

    def _to_rle(self):
        """Generate an RLE array from the ``RasterField`` feature."""
        data = self.feature.bands[0].data  # TODO: is this correct?
        binary_mask = np.asfortranarray(data)
        rle = {'counts': [], 'size': list(binary_mask.shape)}
        counts = rle.get('counts')
        for i, (value, elements) in enumerate(groupby(binary_mask.ravel(order='F'))):
            if i == 0 and value == 1:
                counts.append(0)
            counts.append(len(list(elements)))
        return rle


class Annotation(ModifiableEntry):
    """Image annotation/label for ``ImageEntry``."""

    image = models.ForeignKey(ImageEntry, on_delete=models.CASCADE)

    caption = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=100, blank=True, null=True)
    annotator = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(null=True, blank=True)

    segmentation = models.OneToOneField(Segmentation, null=True, on_delete=models.CASCADE)
    keypoints = models.MultiPointField(null=True, srid=0)
    line = models.LineStringField(null=True, srid=0)
