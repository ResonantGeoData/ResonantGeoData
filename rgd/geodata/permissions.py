from typing import Optional

from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied
from django.db.models.functions import Coalesce

from rgd.geodata import models


def annotate_queryset(queryset):
    """Annotate the queryset to include a path to a collection.

    Some models don't have a direct path to `collection`
    and must be annotated to include it.
    """
    model = queryset.model
    if model == models.SpatialEntry:
        return queryset.annotate(
            _collection_memberships__user=Coalesce(
                'fmventry__fmv_file__file__collection__collection_memberships__user',
                'geometryentry__geometry_archive__file__collection__collection_memberships__user',
                'rastermetaentry__parent_raster__image_set__images__image_file__file__collection__collection_memberships__user',
            ),
            _collection_memberships__role=Coalesce(
                'fmventry__fmv_file__file__collection__collection_memberships__role',
                'geometryentry__geometry_archive__file__collection__collection_memberships__role',
                'rastermetaentry__parent_raster__image_set__images__image_file__file__collection__collection_memberships__role',
            ),
        )
    return queryset


def get_collection_membership_path(model) -> Optional[str]:
    """Get the path to the 'CollectionMembership' model.

    Relationships are represented as 'dunder's ('__'). Returning `None`
    means the model is explicitly unprotected.
    """
    # Collection
    if issubclass(model, models.CollectionMembership):
        return ''
    if issubclass(model, models.Collection):
        return 'collection_memberships'
    # Common
    if issubclass(model, models.ChecksumFile):
        return 'collection__collection_memberships'
    # Imagery
    if issubclass(model, models.ImageEntry):
        return 'image_file__file__collection__collection_memberships'
    if issubclass(model, models.Thumbnail):
        return 'image_entry__image_file__file__collection__collection_memberships'
    if issubclass(model, models.ImageSet):
        return 'images__image_file__file__collection__collection_memberships'
    if issubclass(model, models.RasterEntry):
        return 'image_set__images__image_file__file__collection__collection_memberships'
    if issubclass(model, models.RasterMetaEntry):
        return (
            'parent_raster__image_set__images__image_file__file__collection__collection_memberships'
        )
    if issubclass(model, models.BandMetaEntry):
        return 'parent_image__image_file__file__collection__collection_memberships'
    if issubclass(model, models.ConvertedImageFile):
        return 'source_image__image_file__file__collection__collection_memberships'
    if issubclass(model, models.SubsampledImage):
        return 'source_image__image_file__file__collection__collection_memberships'
    if issubclass(model, models.KWCOCOArchive):
        return 'spec_file__collection__collection_memberships'
    # Annotation
    if issubclass(model, models.Annotation):
        return 'image__image_file__collection__collection_memberships'
    if issubclass(model, models.Segmentation):
        return 'annotation__image__image_file__collection__collection_memberships'
    # Geometry
    if issubclass(model, models.GeometryEntry):
        return 'geometry_archive__file__collection__collection_memberships'
    # FMV
    if issubclass(model, models.FMVEntry):
        return 'fmv_file__file__collection__collection_memberships'
    # SpatialEntry
    if model == models.SpatialEntry:
        return '_collection_memberships'

    raise NotImplementedError


def filter_perm(user, queryset, role):
    """Filter a queryset."""
    # Called outside of view
    if user is None:
        return queryset
    # Admins can see all
    if user.is_active and (user.is_staff or user.is_superuser):
        return queryset
    # No relationship to collection
    path = get_collection_membership_path(queryset.model)
    if path is None:
        return queryset
    # Must be logged in
    if not user.is_active or user.is_anonymous:
        return queryset.none()
    # Check permissions
    # `path` can be an empty string (meaning queryset is `CollectionMembership`)
    user_path = (path + '__' if path != '' else path) + 'user'
    role_path = (path + '__' if path != '' else path) + 'role'
    queryset = annotate_queryset(queryset)
    return queryset.filter(**{user_path: user.pk}).exclude(**{role_path + '__lt': role})


def filter_read_perm(user, queryset):
    """Filter a queryset to what the user may edit."""
    return filter_perm(user, queryset, models.CollectionMembership.READER)


def filter_write_perm(user, queryset):
    """Filter a queryset to what the user may edit."""
    return filter_perm(user, queryset, models.CollectionMembership.OWNER)


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
