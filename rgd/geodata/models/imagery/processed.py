from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from ... import tasks
from ..common import ChecksumFile, ModifiableEntry
from ..mixins import TaskEventMixin
from .base import ImageEntry


class ConvertedImageFile(ModifiableEntry, TaskEventMixin):
    """A model to store converted versions of a raster entry."""

    task_funcs = (tasks.task_convert_to_cog,)
    converted_file = models.OneToOneField(ChecksumFile, on_delete=models.SET_NULL, null=True)
    source_image = models.OneToOneField(ImageEntry, on_delete=models.CASCADE)

    def _post_delete(self, *args, **kwargs):
        # Cleanup the associated ChecksumFile
        if self.converted_file:
            self.converted_file.delete()


class SubsampledImage(ModifiableEntry, TaskEventMixin):
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
