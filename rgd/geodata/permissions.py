from django.contrib.auth.backends import BaseBackend
from django.core.exceptions import PermissionDenied

from rgd.geodata import models


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
