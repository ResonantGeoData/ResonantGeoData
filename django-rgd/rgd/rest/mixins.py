"""Django REST framework style mixins for views and viewsets."""
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rgd.permissions import CollectionAuthorization, CollectionAuthorizationFilter


class BaseRestViewMixin:
    permission_classes = [CollectionAuthorization, IsAuthenticated]
    filter_backends = [CollectionAuthorizationFilter, DjangoFilterBackend]


class TaskEventViewSetMixin:
    """
    Mixin for any TaskEventMixin model.

    Provides the `status` action to retrieve the status of a
    model's task event.

    TODO: This should use a serializer instead.
    """

    @swagger_auto_schema(
        method='GET',
        operation_summary='Check the status.',
    )
    @action(detail=True)
    def status(self, *args, **kwargs):
        obj = self.get_object()
        data = {
            'pk': obj.pk,
            'model': obj.__name__,
            'status': obj.status,
        }
        return Response(data)
