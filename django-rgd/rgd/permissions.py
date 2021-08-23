from typing import List

from django.apps import apps
from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied
from django.db.models import Model, Q
from rgd import models


# get django model via name, regardless of app
def get_model(model_name):
    for m in apps.get_models():
        if m.__name__ == model_name:
            return m


def get_subclasses(model):
    """Retrieve all model subclasses for the provided class excluding the model class itself."""
    return set([m for m in apps.get_models() if issubclass(m, model) and m != model])


def get_permissions_paths(model, target_model) -> List[str]:
    """Get all possible paths to the 'target_model'.

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
    subquery = queryset.none()
    # Now grab resources created by this user - only file-based models
    if not issubclass(queryset.model, (models.CollectionPermission, models.Collection)):
        for path in get_permissions_paths(queryset.model, models.ChecksumFile):
            created_by_path = (path + '__' if path != '' else path) + 'created_by'
            condition = Q(**{created_by_path: user})
            subquery = subquery.union(queryset.filter(condition).values('pk'))
    for path in get_permissions_paths(queryset.model, models.CollectionPermission):
        # `path` can be an empty string (meaning queryset is `CollectionPermission`)
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
