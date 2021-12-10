from collections import deque
import dataclasses
from dataclasses import dataclass
from itertools import chain
from typing import Any, Deque, Iterator, Optional, Type, Union

from django.conf import settings
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Model, Q, QuerySet
from django.db.models.fields.related import OneToOneRel, RelatedField
from rest_framework import filters, permissions
from rgd import models
from typing_extensions import TypeGuard

PathField = Union[RelatedField, OneToOneRel]


def is_path_field(field: Any) -> TypeGuard[PathField]:
    """Check if a `field` is a `PathField`."""
    is_parent = isinstance(field, OneToOneRel) and field.parent_link
    is_forward = isinstance(field, RelatedField)
    return is_parent or is_forward


def get_related_fields(model: Type[Model]) -> Iterator[PathField]:
    """Get all `PathField`s for a `model`."""
    for field in model._meta.get_fields():
        if is_path_field(field):
            yield field


def get_related_field(model: Type[Model], field_name: str) -> PathField:
    """Get a `PathField` for a `model` by its field name."""
    field = model._meta.get_field(field_name)
    if is_path_field(field):
        return field
    raise ValueError(f'{field} is not a `PathField`')


@dataclass
class IdentityPathField:
    """A self referential field used to represent a root node."""

    model: Type[Model]

    @property
    def related_model(self) -> Type[Model]:
        return self.model


@dataclass
class Path:
    """Singly linked list of `PathField`s."""

    field: Union[PathField, IdentityPathField]
    previous: Optional['Path'] = dataclasses.field(default=None, init=False)

    def traverse(self) -> Iterator['Path']:
        """Iterate backwards over the linked paths."""
        path: Optional['Path'] = self
        while path is not None:
            yield path
            path = path.previous

    def has_visited(self, model: Type[Model]) -> bool:
        """Return whether this path has visited the given `model`."""
        return any(
            path.field.related_model == model or path.field.model == model
            for path in self.traverse()
        )

    def get_frontier(self) -> Iterator['Path']:
        """Iterate over the paths in this path's frontier."""
        for field in get_related_fields(self.field.related_model):
            if not self.has_visited(field.related_model):
                path = Path(field)
                path.previous = self
                yield path

    def q(self, **kwargs: Any) -> Q:
        """Return a `Q` object for this path.

        Can be any keyword arguments i.e. `user__isnull=True`.
        """
        conditions = Q()
        field_names = reversed(
            tuple(
                path.field.name
                for path in self.traverse()
                if not isinstance(path.field, IdentityPathField)
            )
        )
        for key, value in kwargs.items():
            dunder = '__'.join(chain(field_names, (key,)))
            conditions &= Q(**{dunder: value})
        return conditions


def get_paths(source: Type[Model], target: Type[Model]) -> Iterator[Path]:
    """Get all paths from a `source` model to a `target` model.

    Cycles are prevented by not following models that have already been
    visited. This means that recursive relationships will only be followed
    to a depth of 1.

    Only "forward" relationships are followed. This includes
    parent -> child relationships for inherited models.

    This performs a breadth-first search, so shorter paths will be
    returned first.
    """
    queue: Deque[Path] = deque()
    queue.append(Path(IdentityPathField(source)))

    while queue:
        path = queue.pop()
        if path.field.related_model == target:
            yield path
            continue
        frontier = path.get_frontier()
        queue.extendleft(frontier)


def filter_perm(user, queryset, role):
    """Filter a queryset.

    Main authorization business logic goes here.
    """
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
    conditions = []
    model = queryset.model
    paths_to_checksumfile = [*get_paths(model, models.ChecksumFile)]
    if model == models.Collection:
        # Add custom reverse relationships
        field = model._meta.get_field('checksumfiles')
        path = Path(field)
        paths_to_checksumfile.append(path)
    for path in paths_to_checksumfile:
        # A user can read/write a file if they are the creator
        is_creator = path.q(created_by=user)
        conditions.append(is_creator)
        if (
            getattr(settings, 'RGD_GLOBAL_READ_ACCESS', False)
            and role == models.CollectionPermission.READER
        ):
            # A user can read any file by default
            has_no_owner = path.q(created_by__isnull=True)
            conditions.append(has_no_owner)
    for path in get_paths(model, models.Collection):
        # Check collection permissions
        has_permission = path.q(collection_permissions__user=user)
        has_role_level = path.q(collection_permissions__role__gte=role)
        conditions.append(has_permission & has_role_level)
    whitelist = (
        queryset.none()
        .union(*(queryset.filter(condition) for condition in conditions), all=True)
        .values('pk')
    )
    return queryset.filter(pk__in=whitelist)


def filter_read_perm(user, queryset):
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


class CollectionAuthorization(permissions.BasePermission):
    """A custom Django REST Framework permission backend.

    Object-level permission to only allow owners of an object to edit it
    and readers to view it. This will not filter the queryset in 'list' views.
    You should use this in combination with the `CollectionAuthorizationFilter` to
    also filter the queryset in 'list' views.

    https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions
    """

    def has_object_permission(self, request, view, obj):
        # Check read permissions for GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            check_read_perm(request.user, obj)
        else:
            check_write_perm(request.user, obj)
        # The above calls should raise an exception if the user does not have permissions.
        return True


class CollectionAuthorizationFilter(filters.BaseFilterBackend):
    """A custom Django REST Framework filter backend for permissions.

    As a result of applying this filter, objects that the user does not have persmissions
    to view will return a '404' since the queryset is filtered before object-level
    permissions are checked.

    https://www.django-rest-framework.org/api-guide/permissions/#custom-permissions
    """

    def filter_queryset(self, request, queryset, view):
        # Check read permissions for GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return filter_read_perm(request.user, queryset)
        # Otherwise, assume this is a writable query.
        return filter_write_perm(request.user, queryset)
