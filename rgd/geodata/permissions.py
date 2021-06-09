from typing import List

from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied
from django.db.models import Q

from rgd.geodata import models


def get_collection_permissions_paths(model) -> List[str]:
    """Get all possible paths to the 'CollectionPermission' model.

    Relationships are represented as 'dunder's ('__').
    """
    # Collection
    if issubclass(model, models.CollectionPermission):
        return ['']
    if issubclass(model, models.Collection):
        return ['collection_permissions']
    # Common
    if issubclass(model, models.ChecksumFile):
        return ['collection__collection_permissions']
    # Imagery
    if issubclass(model, models.ImageEntry):
        return ['image_file__file__collection__collection_permissions']
    if issubclass(model, models.ImageSet):
        return ['images__image_file__file__collection__collection_permissions']
    if issubclass(model, models.RasterEntry):
        return ['image_set__images__image_file__file__collection__collection_permissions']
    if issubclass(model, models.RasterMetaEntry):
        return [
            'parent_raster__image_set__images__image_file__file__collection__collection_permissions'
        ]
    if issubclass(model, models.BandMetaEntry):
        return ['parent_image__image_file__file__collection__collection_permissions']
    if issubclass(model, models.ConvertedImageFile):
        return ['source_image__image_file__file__collection__collection_permissions']
    if issubclass(model, models.SubsampledImage):
        return ['source_image__image_file__file__collection__collection_permissions']
    if issubclass(model, models.KWCOCOArchive):
        return ['spec_file__collection__collection_permissions']
    # Annotation
    if issubclass(model, models.Annotation):
        return ['image__image_file__collection__collection_permissions']
    if issubclass(model, models.Segmentation):
        return ['annotation__image__image_file__collection__collection_permissions']
    # Geometry
    if issubclass(model, models.GeometryEntry):
        return ['geometry_archive__file__collection__collection_permissions']
    # FMV
    if issubclass(model, models.FMVEntry):
        return ['fmv_file__file__collection__collection_permissions']
    # Point Cloud
    if issubclass(model, models.PointCloudFile):
        return ['file__collection__collection_permissions']
    if issubclass(model, models.PointCloudEntry):
        return [
            'source__file__collection__collection_permissions',
            'vtp_data__collection__collection_permissions',
        ]
    # ImageSetSpatial
    if issubclass(model, models.ImageSetSpatial):
        return ['image_set__images__image_file__file__collection__collection_permissions']
    # SpatialEntry
    if model == models.SpatialEntry:
        return [
            'fmventry__fmv_file__file__collection__collection_permissions',
            'geometryentry__geometry_archive__file__collection__collection_permissions',
            'rastermetaentry__parent_raster__image_set__images__image_file__file__collection__collection_permissions',
            'imagesetspatial__image_set__images__image_file__file__collection__collection_permissions',
        ]

    raise NotImplementedError


def filter_perm(user, queryset, role):
    """Filter a queryset."""
    # Called outside of view
    if user is None:
        return queryset
    # Must be logged in
    if not user.is_active or user.is_anonymous:
        return queryset.none()
    # Superusers can see all (not staff users)
    if user.is_active and user.is_superuser:
        return queryset
    # Check permissions
    # `path` can be an empty string (meaning queryset is `CollectionPermission`)
    paths = get_collection_permissions_paths(queryset.model)
    subquery = queryset.none()
    for path in paths:
        user_path = (path + '__' if path != '' else path) + 'user'
        role_path = (path + '__' if path != '' else path) + 'role'
        condition = Q(**{user_path: user}) & Q(**{role_path + '__lt': role})
        if settings.RGD_GLOBAL_READ_ACCESS:
            condition |= Q(**{path + '__isnull': True})
        subquery = subquery.union(queryset.filter(condition).values('pk'))
    return queryset.filter(pk__in=subquery)


def filter_read_perm(user, queryset):
    """Filter a queryset to what the user may read."""
    return filter_perm(user, queryset, models.CollectionPermission.READER)


def filter_write_perm(user, queryset):
    """Filter a queryset to what the user may edit."""
    return filter_perm(user, queryset, models.CollectionPermission.OWNER)


def check_read_perm(user, obj):
    """Raise 'PermissionDenied' error if user does not have read permissions."""
    model = type(obj)
    if not filter_read_perm(user, model.objects.filter(pk=obj.pk)).exists():
        raise PermissionDenied


def check_write_perm(user, obj):
    """Raise 'PermissionDenied' error if user does not have write permissions."""
    # Called outside of view
    model = type(obj)
    if not filter_write_perm(user, model.objects.filter(pk=obj.pk)).exists():
        raise PermissionDenied


class CollectionAuthorizationBackend(BaseBackend):
    def has_perm(self, user, perm, obj=None):
        """Supplement default Django permission backend.

        Returns `True` if the user has the specified permission, where perm is in the format
        `"<app label>.<permission codename>"`. If the user is
        inactive, this method will always return False. For an active superuser, this method
        will always return `True`.

        https://docs.djangoproject.com/en/3.1/ref/contrib/auth/#django.contrib.auth.models.User.has_perm
        """
        app_label, codename = perm.split('.')
        if app_label == 'geodata':
            if codename.startswith('view'):
                check_read_perm(user, obj)
            if (
                codename.startswith('add')
                or codename.startswith('delete')
                or codename.startswith('change')
            ):
                check_write_perm(user, obj)
