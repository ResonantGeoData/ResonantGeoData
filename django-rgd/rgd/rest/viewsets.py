from rgd import models, serializers
from rgd.rest.base import ModelViewSet


class CollectionViewSet(ModelViewSet):
    serializer_class = serializers.CollectionSerializer
    queryset = models.Collection.objects.all()
