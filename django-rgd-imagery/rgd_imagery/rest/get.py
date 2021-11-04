from rest_framework.generics import RetrieveAPIView
from rgd.rest.mixins import BaseRestViewMixin
from rgd_imagery import models, serializers


class GetImageMeta(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.ImageMetaSerializer
    lookup_field = 'pk'
    queryset = models.ImageMeta.objects.all()


class GetImageSet(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.ImageSetSerializer
    lookup_field = 'pk'
    queryset = models.ImageSet.objects.all()


class GetImageSetSpatial(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.ImageSetSpatialSerializer
    lookup_field = 'pk'
    queryset = models.ImageSetSpatial.objects.all()


class GetRasterMeta(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.RasterMetaSerializer
    lookup_field = 'pk'
    queryset = models.RasterMeta.objects.all()


class GetRasterMetaSTAC(BaseRestViewMixin, RetrieveAPIView):
    serializer_class = serializers.stac.ItemSerializer
    lookup_field = 'pk'
    queryset = models.RasterMeta.objects.all()
