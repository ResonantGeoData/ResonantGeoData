from rest_framework import mixins, viewsets
from rgd.rest.mixins import BaseRestViewMixin


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
