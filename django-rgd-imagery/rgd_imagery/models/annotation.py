import base64
import pickle

from django.contrib.gis.db import models
from django.core.exceptions import ObjectDoesNotExist
from django_extensions.db.models import TimeStampedModel
import numpy as np

from .base import Image


class Annotation(TimeStampedModel):
    """Image annotation/label for ``Image``."""

    image = models.ForeignKey(Image, on_delete=models.CASCADE)

    caption = models.CharField(max_length=100, blank=True, null=True)
    label = models.CharField(max_length=100, blank=True, null=True)
    annotator = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(null=True, blank=True)

    keypoints = models.MultiPointField(null=True, srid=0)
    line = models.LineStringField(null=True, srid=0)

    def segmentation_type(self):
        """Get type of segmentation."""
        return self.segmentation.get_type()


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

    annotation = models.OneToOneField(Annotation, on_delete=models.CASCADE)

    # COCO bounding box format is [top left x position, top left y position, width, height]
    # This should come from the COCO format rather than be autopopulated by us
    outline = models.PolygonField(srid=0, null=True, help_text='The bounding box')

    def get_type(self):
        """Get type of segmentation."""
        try:
            _ = self.polygonsegmentation
            return 'PolygonSegmentation'
        except ObjectDoesNotExist:
            pass
        try:
            _ = self.rlesegmentation
            return 'RLE'
        except ObjectDoesNotExist:
            pass
        return 'Oultine/BBox'


class PolygonSegmentation(Segmentation):
    """one/many shape(s) in pixel coordinates (can be decimal).

    Note
    ----
    We use ``MultiPolygonField`` as the segmentation can be multiple
    separated polygons across the image.

    """

    feature = models.MultiPolygonField(srid=0, null=True)


class RLESegmentation(Segmentation):
    """run-length-encoded (RLE) segmentation.

    A bit mask of the entire image to label one thing (or a crowd of that
    thing). The RLE array is stored as a binary blob.

    """

    blob = models.BinaryField()
    height = models.PositiveIntegerField()
    width = models.PositiveIntegerField()

    @staticmethod
    def _array_to_blob(array):
        if not isinstance(array, np.ndarray):
            array = np.array(array)
        return base64.b64encode(pickle.dumps(array))

    @staticmethod
    def _blob_to_array(blob):
        return pickle.loads(base64.b64decode(blob))

    def from_rle(self, rle):
        """Populate the entry from an RLE JSON spec.

        Parameters
        ----------
        rle : dict
            A dictionary with ``counts`` and ``size`` fields
        """
        counts = rle['counts']
        height, width = rle['size']
        self.height = height
        self.width = width
        self.blob = self._array_to_blob(counts)

    def to_rle(self):
        """Generate an RLE JSON spec from the entry."""
        counts = self._blob_to_array(self.blob)
        return {'counts': list(counts), 'size': [self.height, self.width]}

    def to_mask(self):
        """Produce a 2D array of booleans for this RLE Segmentation."""
        counts = self._blob_to_array(self.blob)
        shape = (self.height, self.width)
        mask = np.zeros(shape, dtype=np.bool_).ravel()
        current = 0
        flag = False
        for count in counts:
            mask[current : current + count] = flag
            current += count
            flag = not flag
        return mask.reshape(shape)
