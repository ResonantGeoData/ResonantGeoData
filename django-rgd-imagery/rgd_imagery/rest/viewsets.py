from rgd.rest.base import ModelViewSet
from rgd_imagery import models, serializers


class ProcessedImageViewSet(ModelViewSet):
    serializer_class = serializers.ProcessedImageSerializer
    queryset = models.ProcessedImage.objects.all()
