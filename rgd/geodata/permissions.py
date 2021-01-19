from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied

from rgd.geodata import models


def get_collection_membership_path(model):
    """Get the path to the 'CollectionMembership' model.

    Relationships are represented as 'dunder's ('__').
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
        return 'image_file__collection__collection_memberships'
    if issubclass(model, models.Thumbnail):
        return 'image_entry__image_file__collection__collection_memberships'
    if issubclass(model, models.ImageSet):
        return 'images__image_file__collection__collection_memberships'
    if issubclass(model, models.RasterEntry):
        return 'image_set__images__image_file__collection__collection_memberships'
    if issubclass(model, models.RasterMetaEntry):
        return 'parent_raster__image_set__images__image_file__collection__collection_memberships'
    if issubclass(model, models.BandMetaEntry):
        return 'parent_image__image_file__collection__collection_memberships'
    if issubclass(model, models.ConvertedImageFile):
        return 'source_image__image_file__collection__collection_memberships'
    if issubclass(model, models.SubsampledImage):
        return 'source_image__image_file__collection__collection_memberships'
    if issubclass(model, models.KWCOCOArchive):
        return 'spec_file__collection__collection_memberships'
    # Annotation
    if issubclass(model, models.Annotation):
        return 'image__image_file__collection__collection_memberships'
    if issubclass(model, models.Segmentation):
        return 'annotation__image__image_file__collection__collection_memberships'
    # Geometry
    if issubclass(model, models.GeometryEntry):
        return 'geometry_archive__collection__collection_memberships'
    # FMV
    if issubclass(model, models.FMVEntry):
        return 'fmv_file__collection__collection_memberships'
    return None


def filter_read_perm(user, queryset):
    """Filter a queryset to what the user may see."""
    # Called outside of view
    if user is None:
        return queryset
    path = get_collection_membership_path(queryset.model)
    # No relationship to collection
    if path is None:
        return queryset
    # Must be logged in
    if not user.is_active or user.is_anonymous:
        return queryset.none()
    # Admins can see all
    if user.is_active and (user.is_staff or user.is_superuser):
        return queryset
    # Check permissions
    user_path = (path + '__' if path != '' else path) + 'user'
    role_path = (path + '__' if path != '' else path) + 'role'
    return queryset.filter(
        **{
            user_path: user,
            role_path + '__gte': models.CollectionMembership.READER,
        }
    )


class CollectionAuthorizationBackend(BaseBackend):
    def has_perm(self, user, perm, obj=None):
        """Returns `True` if the user has the specified permission, where perm is in the format
        `"<app label>.<permission codename>"`. If the user is
        inactive, this method will always return False. For an active superuser, this method
        will always return `True`.

        https://docs.djangoproject.com/en/3.1/ref/contrib/auth/#django.contrib.auth.models.User.has_perm
        """
        app_label, codename = perm.split('.')
        # Permissions only apply to 'geodata' app
        if app_label != 'geodata':
            return False
        # Only the collection "owner" can alter their own `CollectionMembership` and `Collection` objects.
        if (
            isinstance(obj, models.CollectionMembership)
            and not models.CollectionMembership.objects.filter(
                collection=obj.collection,
                user=user,
                role=models.CollectionMembership.OWNER,
            ).exists()
        ):
            raise PermissionDenied
        if (
            isinstance(obj, models.Collection)
            and not models.CollectionMembership.objects.filter(
                collection=obj,
                user=user,
                role=models.CollectionMembership.OWNER,
            ).exists()
        ):
            raise PermissionDenied
