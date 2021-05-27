from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.gis.admin import OSMGeoAdmin

from . import actions
from .models.collection import Collection, CollectionPermission
from .models.common import ChecksumFile, WhitelistedEmail
from .models.fmv import FMVEntry, FMVFile
from .models.geometry import GeometryArchive, GeometryEntry
from .models.imagery import (
    Annotation,
    BandMetaEntry,
    ConvertedImageFile,
    ImageEntry,
    ImageFile,
    ImageSet,
    KWCOCOArchive,
    PolygonSegmentation,
    RasterEntry,
    RasterMetaEntry,
    RLESegmentation,
    Segmentation,
    SubsampledImage,
)
from .models.threed.point_cloud import PointCloudEntry, PointCloudFile, PointCloudMetaEntry

MODIFIABLE_FILTERS = (
    'modified',
    'created',
)

SPATIAL_ENTRY_FILTERS = (
    'acquisition_date',
    'instrumentation',
)

TASK_EVENT_FILTERS = ('status',)

TASK_EVENT_READONLY = (
    'failure_reason',
    'status',
)

admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    actions = [
        actions.make_users_active,
        actions.make_users_staff,
    ]

    list_display = (
        'username',
        'is_staff',
        'is_superuser',
        'is_active',
    )


class _FileGetNameMixin:
    def get_name(self, obj):
        return obj.file.name

    get_name.short_description = 'Name'
    get_name.admin_order_field = 'file__name'


@admin.register(WhitelistedEmail)
class WhitelistedEmailAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'email',
    )


@admin.register(ChecksumFile)
class ChecksumFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'modified',
        'created',
        'type',
        'data_link',
        'collection',
    )
    readonly_fields = (
        'checksum',
        'last_validation',
    ) + TASK_EVENT_READONLY
    actions = (actions.reprocess, actions.make_image_files)
    list_filter = (
        MODIFIABLE_FILTERS
        + TASK_EVENT_FILTERS
        + (
            'type',
            'collection',
        )
    )


@admin.register(KWCOCOArchive)
class KWCOCOArchiveAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'modified',
        'created',
    )
    readonly_fields = ('image_set',) + TASK_EVENT_READONLY
    actions = (actions.reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


@admin.register(ImageSet)
class ImageSetAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'count',
        'modified',
        'created',
    )
    actions = (
        actions.make_raster_from_image_set,
        actions.clean_empty_image_sets,
    )
    list_filter = MODIFIABLE_FILTERS


class BandMetaEntryInline(admin.StackedInline):
    model = BandMetaEntry
    fk_name = 'parent_image'

    list_display = (
        'id',
        'parent_image',
        'modified',
        'created',
    )
    readonly_fields = (
        'mean',
        'max',
        'min',
        'modified',
        'created',
        'parent_image',
        'std',
        'nodata_value',
        'dtype',
        'band_number',
    )

    def has_add_permission(self, request, obj=None):
        """Prevent user from adding more."""
        return False


@admin.register(ImageEntry)
class ImageEntryAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'image_file',
        'modified',
        'created',
    )
    readonly_fields = (
        'number_of_bands',
        'image_file',
        'height',
        'width',
        'driver',
        'modified',
        'created',
    )
    list_filter = MODIFIABLE_FILTERS + (
        'number_of_bands',
        'driver',
    )
    actions = (
        actions.make_image_set_from_image_entries,
        actions.make_raster_from_image_entries,
        actions.make_raster_for_each_image_entry,
    )
    inlines = (BandMetaEntryInline,)


@admin.register(RasterMetaEntry)
class RasterMetaEntryAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'acquisition_date',
        'modified',
        'created',
    )
    readonly_fields = (
        'crs',
        'origin',
        'extent',
        'resolution',
        'transform',
        'parent_raster',
        'modified',
        'created',
    )
    actions = (
        actions.reprocess_rastermeta,
        actions.generate_valid_data_footprint_rastermeta,
    )
    list_filter = SPATIAL_ENTRY_FILTERS + MODIFIABLE_FILTERS

    modifiable = False  # To still show the footprint and outline


@admin.register(RasterEntry)
class RasterEntryAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'name',
        'status',
        'count',
        'acquisition_date',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    actions = (
        actions.reprocess,
        actions.generate_valid_data_footprint,
        actions.clean_empty_rasters,
    )
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


class SegmentationInline(admin.StackedInline):
    model = Segmentation
    fk_name = 'annotation'
    list_display = ('id',)
    readonly_fields = ('outline',)


class PolygonSegmentationInline(admin.StackedInline):
    model = PolygonSegmentation
    fk_name = 'annotation'
    list_display = ('id',)
    readonly_fields = (
        'outline',
        'feature',
    )


class RLESegmentationInline(admin.StackedInline):
    model = RLESegmentation
    fk_name = 'annotation'
    list_display = ('id',)
    readonly_fields = ('outline', 'width', 'height', 'blob')


@admin.register(Annotation)
class AnnotationAdmin(OSMGeoAdmin):
    list_display = (
        'id',
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


@admin.register(ImageFile)
class ImageFileAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'id',
        'get_name',
        'status',
        'modified',
        'created',
        'image_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    actions = (actions.reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


@admin.register(ConvertedImageFile)
class ConvertedImageFileAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'source_image',
        'status',
        'modified',
        'created',
    )
    readonly_fields = ('converted_file',) + TASK_EVENT_READONLY
    actions = (actions.reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


@admin.register(SubsampledImage)
class SubsampledImageAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'source_image',
        'sample_type',
        'status',
        'modified',
        'created',
    )
    readonly_fields = ('data',) + TASK_EVENT_READONLY
    actions = (actions.reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


class GeometryEntryInline(admin.StackedInline):
    model = GeometryEntry
    fk_name = 'geometry_archive'
    list_display = (
        'id',
        'name',
        'geometry_archive',
        'modified',
        'created',
    )
    list_filter = MODIFIABLE_FILTERS + SPATIAL_ENTRY_FILTERS
    readonly_fields = (
        'modified',
        'created',
        'geometry_archive',
    )
    modifiable = False  # To still show the footprint and outline


@admin.register(GeometryArchive)
class GeometryArchiveAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'id',
        'get_name',
        'status',
        'modified',
        'created',
        'archive_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    inlines = (GeometryEntryInline,)
    actions = (actions.reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


class FMVEntryInline(admin.StackedInline):
    model = FMVEntry
    fk_name = 'fmv_file'
    list_display = (
        'id',
        'name',
        'fmv_file',
        'modified',
        'created',
    )
    readonly_fields = (
        'modified',
        'created',
    )


@admin.register(FMVFile)
class FMVFileAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'id',
        'get_name',
        'status',
        'modified',
        'created',
        'fmv_data_link',
        'klv_data_link',
    )
    readonly_fields = (
        'modified',
        'created',
        'klv_file',
        'web_video_file',
        'frame_rate',
    ) + TASK_EVENT_READONLY
    inlines = (FMVEntryInline,)
    actions = (actions.reprocess,)
    list_filter = MODIFIABLE_FILTERS


class CollectionPermissionInline(admin.TabularInline):
    model = CollectionPermission
    fk_name = 'collection'
    fields = ('user', 'role')
    extra = 1


@admin.register(Collection)
class CollectionAdmin(OSMGeoAdmin):
    fields = ('name',)
    inlines = (CollectionPermissionInline,)


@admin.register(PointCloudFile)
class PointCloudFileAdmin(OSMGeoAdmin, _FileGetNameMixin):
    list_display = (
        'id',
        'get_name',
        'status',
        'modified',
        'created',
        'data_link',
    )
    readonly_fields = (
        'modified',
        'created',
    ) + TASK_EVENT_READONLY
    actions = (actions.reprocess,)
    list_filter = MODIFIABLE_FILTERS + TASK_EVENT_FILTERS


class PointCloudMetaEntryInline(admin.StackedInline):
    model = PointCloudMetaEntry
    fk_name = 'parent_point_cloud'
    list_display = (
        'id',
        'modified',
        'created',
        'crs',
    )
    readonly_fields = (
        'modified',
        'created',
        'parent_point_cloud',
    )
    modifiable = False  # To still show the footprint and outline


@admin.register(PointCloudEntry)
class PointCloudEntryAdmin(OSMGeoAdmin):
    list_display = (
        'id',
        'modified',
        'created',
        'data_link',
    )
    readonly_fields = (
        'modified',
        'created',
    )
    inlines = (PointCloudMetaEntryInline,)
    list_filter = MODIFIABLE_FILTERS
