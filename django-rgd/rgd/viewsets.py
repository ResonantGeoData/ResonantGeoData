from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets


class BaseViewMixin:
    filter_backends = [DjangoFilterBackend]


class ReadOnlyModelViewSet(
    BaseViewMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """A viewset for read models.

    Provides default `list()` and `retrieve()` actions.
    """

    pass


class ModelViewSet(
    BaseViewMixin,
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
