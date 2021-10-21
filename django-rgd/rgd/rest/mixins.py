"""Django REST framework style mixins for views."""
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rgd.permissions import CollectionAuthorization, CollectionAuthorizationFilter


class BaseRestViewMixin:
    permission_classes = [CollectionAuthorization, IsAuthenticated]
    filter_backends = [CollectionAuthorizationFilter, DjangoFilterBackend]
