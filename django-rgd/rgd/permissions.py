from typing import List

from django.apps import apps
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from rgd import models


def get_subclasses(model):
    """Retrieve all model subclasses for the provided class excluding the model class itself."""
    return set([m for m in apps.get_models() if issubclass(m, model) and m != model])


def get_collection_permissions_paths(model, prefix='') -> List[str]:
    """Get all possible paths to the 'CollectionPermission' model.

    Relationships are represented as 'dunder's ('__').
    """
    if model == models.SpatialEntry:
        submodels = get_subclasses(model)
        paths = []
        for sub in submodels:
            # TODO: there should be a cleaner way to do this.
            model_name = sub.__name__.lower()
            [paths.append(s) for s in get_collection_permissions_paths(sub, prefix=model_name)]
        return paths

    if not hasattr(model, 'permissions_paths'):
        # NOTE: checking subclass here does not work - must use hasattr :(
        raise TypeError(f'{type(model)} does not have the `PermissionPathMixin` interface.')

    return [(f'{prefix}__' if prefix else '') + s for s in model.permissions_paths]


def filter_perm(user, queryset, role):
    """Filter a queryset."""
    if queryset.model == models.SpatialEntry:
        # Return subclasses of SpatialEntry
        queryset = queryset.select_subclasses()
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
        if getattr(settings, 'RGD_GLOBAL_READ_ACCESS', False):
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
