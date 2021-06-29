from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.admin.mixins import MODIFIABLE_FILTERS
from rgd_imagery.models import Annotation, PolygonSegmentation, RLESegmentation, Segmentation


class SegmentationInline(admin.StackedInline):
    model = Segmentation
    fk_name = 'annotation'
    list_display = ('pk',)
    readonly_fields = ('outline',)


class PolygonSegmentationInline(admin.StackedInline):
    model = PolygonSegmentation
    fk_name = 'annotation'
    list_display = ('pk',)
    readonly_fields = (
        'outline',
        'feature',
    )


class RLESegmentationInline(admin.StackedInline):
    model = RLESegmentation
    fk_name = 'annotation'
    list_display = ('pk',)
    readonly_fields = ('outline', 'width', 'height', 'blob')


@admin.register(Annotation)
class AnnotationAdmin(OSMGeoAdmin):
    list_display = (
        'pk',
        'caption',
        'label',
        'annotator',
        'segmentation_type',
        'modified',
        'created',
    )
    readonly_fields = (
        'keypoints',
        'line',
    )
    inlines = (SegmentationInline, PolygonSegmentationInline, RLESegmentationInline)
    list_filter = MODIFIABLE_FILTERS + (
        'annotator',
        'label',
    )
