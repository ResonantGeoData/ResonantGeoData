from functools import reduce
from operator import __or__ as OR  # noqa
from typing import List

from django.apps import apps
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Model, Q, QuerySet
from rgd import models


def get_user_collections(user: User, role: int):
    """Get the Collections that the user has access to at or above the given role.

    Note
    ----
    This handles the `RGD_GLOBAL_READ_ACCESS` setting and will return all
    collections with null permissions if the setting is enabled.

    Parameters
    ----------
    role: int
        The minimum role (see CollectionPermission.ROLE_CHOICES) of the
        user for the collections. To get all of the collections that
        the user is an "owner" of, pass 2 as the role.

    """
    queryset = models.Collection.objects.all()
    # Must be logged in
    if user is None or not user.is_active or user.is_anonymous:
        return queryset.none()
    # Superusers can see all (not staff users)
    if user.is_superuser:
        return queryset
    # Else, check user permissions
    condition = Q(collection_permissions__user=user) & Q(
        **{'collection_permissions__role__gte': role}
    )
    if getattr(settings, 'RGD_GLOBAL_READ_ACCESS', False):
        condition |= Q(**{'collection_permissions__isnull': True})
    return queryset.filter(condition)


# get django model via name, regardless of app
def get_model(model_name: str):
    for m in apps.get_models():
        if m.__name__ == model_name:
            return m


def get_subclasses(model: Model):
    """Retrieve all model subclasses for the provided class excluding the model class itself."""
    return set(
        [
            m
            for m in apps.get_models()
            if issubclass(m, model)
            and m != model
            and issubclass(m, models.mixins.PermissionPathMixin)
        ]
    )


def get_permissions_paths(model: Model, target_model: Model) -> List[str]:
    """Get all possible paths to the 'target_model'.

    Note
    ----
    Produces relationships represented as 'dunder's ('__').

    """
    if model == target_model:
        return ['']

    if model == models.SpatialEntry:
        submodels = get_subclasses(model)
        paths = []
        for sub in submodels:
            # TODO: there should be a cleaner way to do this.
            model_name = sub.__name__.lower()
            [paths.append(f'{model_name}__{s}') for s in get_permissions_paths(sub, target_model)]
        return paths

    if not issubclass(model, models.mixins.PermissionPathMixin):
        raise TypeError(f'{type(model)} does not have the `PermissionPathMixin` interface.')

    paths = []
    for path in model.permissions_paths:
        field, next_model = path

        if type(next_model) == str:

            # grab model via class name
            next_model = get_model(next_model)

        # sanity check
        if not issubclass(next_model, Model):
            raise TypeError('Failed to extract next_model in permissions_paths')

        if next_model == target_model:
            paths.append(field)
        else:
            next_path = get_permissions_paths(next_model, target_model)
            for n in next_path:
                paths.append(f'{field}__{n}')

    return paths


def filter_created_by_user(user: User, queryset: QuerySet, default_only: bool = False):
    """Filter a queryset to all files that were created by the given user.

    Parameters
    ----------
    default_only: bool
        This will filter for the user's "default collection". A user's
        "default collection" are all of the files `created_by` that user
        that do not have a `collection` assigned. For more details, see
        https://github.com/ResonantGeoData/ResonantGeoData/issues/474

    Warning
    -------
    This cannot filter a queryset of `Collection` or `CollectionPermission` objects.

    """
    if issubclass(queryset.model, (models.CollectionPermission, models.Collection)):
        raise TypeError(f'`filter_created_by_user` does not handle querysets of {queryset.model}')
    paths = get_permissions_paths(queryset.model, models.ChecksumFile)
    condition = reduce(
        OR,
        [Q(**{(path + '__' if path != '' else path) + 'created_by': user}) for path in paths],
    )
    if default_only:
        paths = get_permissions_paths(queryset.model, models.Collection)
        condition &= reduce(OR, [Q(**{f'{path}__isnull': True}) for path in paths])
    return queryset.filter(condition)


def filter_collections(queryset: QuerySet, collections: List[models.Collection]):
    """Filter a queryset by a list of Collections.

    Note
    ----
    This does not check user roles / user access. It simply filters by a list
    of given Collection records. This is often used with `get_user_collections`
    which does check the user permissions and handles `RGD_GLOBAL_READ_ACCESS`.

    """
    # Handle CollectionPermission and Collection as special cases
    if issubclass(queryset.model, models.CollectionPermission):
        return queryset.filter(collection__pk__in=collections)
    if issubclass(queryset.model, models.Collection):
        return queryset.filter(pk__in=collections)
    # Handle all other models by getting the path to Collection
    paths = get_permissions_paths(queryset.model, models.Collection)
    condition = reduce(OR, [Q(**{f'{path}__in': collections}) for path in paths])
    # distinct is necessary here when this filter is paired with other filters
    # e.g., in SpatialEntryFilter
    return queryset.filter(condition).distinct()


def filter_perm(user: User, queryset: QuerySet, role: int):
    """Filter a queryset."""
    if queryset.model == models.SpatialEntry:
        # Return subclasses of SpatialEntry
        queryset = queryset.select_subclasses()
    # Called outside of view
    if user is None:
        # TODO: I think this is used if a user isn't logged in and hits our endpoints which is a problem
        return queryset
    # Must be logged in
    if not user.is_active or user.is_anonymous:
        return queryset.none()
    # Superusers can see all (not staff users)
    if user.is_active and user.is_superuser:
        return queryset
    # Check permissions
    subquery = queryset.none()
    # Now grab resources created by this user - only file-based models
    if not issubclass(queryset.model, (models.CollectionPermission, models.Collection)):
        # NOTE: `default_only` is False here. This is because there exists a scenario where
        #       a user may have created a file (giving them OWNER access) but the user
        #       may not have been added to the file's Collection. This scenario is tested
        #       by `test_nonadmin_created_by_permissions`.
        subquery = subquery.union(filter_created_by_user(user, queryset, default_only=False))
    # Now filter data that belong to a collection which the user has access at the specified role
    user_collections = get_user_collections(user, role)
    subquery = subquery.union(filter_collections(queryset, user_collections)).values('pk')
    # Distinct is necessary because of the overlap in `filter_created_by_user` and `filter_collections`
    return queryset.filter(pk__in=subquery).distinct()


def filter_read_perm(user: User, queryset: QuerySet):
    """Filter a queryset to what the user may read."""
    return filter_perm(user, queryset, models.CollectionPermission.READER)


def filter_write_perm(user: User, queryset: QuerySet):
    """Filter a queryset to what the user may edit."""
    return filter_perm(user, queryset, models.CollectionPermission.OWNER)


def check_read_perm(user: User, obj: Model):
    """Raise 'PermissionDenied' error if user does not have read permissions."""
    model = type(obj)
    if not filter_read_perm(user, model.objects.filter(pk=obj.pk)).exists():
        raise PermissionDenied


def check_write_perm(user: User, obj: Model):
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
