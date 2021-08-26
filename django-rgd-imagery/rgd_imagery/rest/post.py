from rest_framework.generics import CreateAPIView
from rgd_imagery import models, serializers


class CreateConvertedImage(CreateAPIView):
    queryset = models.ConvertedImage.objects.all()
    serializer_class = serializers.ConvertedImageSerializer


class CreateRegionImage(CreateAPIView):
    queryset = models.RegionImage.objects.all()
    serializer_class = serializers.RegionImageSerializer


class CreateRasterSTAC(CreateAPIView):
    queryset = models.RasterMeta.objects.all()
    serializer_class = serializers.STACRasterFeatureSerializer


class CreateImage(CreateAPIView):
    queryset = models.Image.objects.all()
    serializer_class = serializers.ImageSerializer


class CreateImageSet(CreateAPIView):
    queryset = models.ImageSet.objects.all()
    serializer_class = serializers.ImageSetSerializer


class CreateImageSetSpatial(CreateAPIView):
    queryset = models.ImageSetSpatial.objects.all()
    serializer_class = serializers.ImageSetSpatialSerializer


class CreateRaster(CreateAPIView):
    queryset = models.Raster.objects.all()
    serializer_class = serializers.RasterSerializer
