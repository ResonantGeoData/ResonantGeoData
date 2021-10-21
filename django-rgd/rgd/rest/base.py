from drf_yasg.utils import swagger_auto_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rgd.rest.mixins import BaseRestViewMixin


class TaskEventViewMixin:
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


class ReadOnlyModelViewSet(
    BaseRestViewMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """A viewset for read models.

    Provides default `list()` and `retrieve()` actions.
    """

    pass


class ModelViewSet(
    BaseRestViewMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    A viewset for read and edit models.

    Provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """

    pass
