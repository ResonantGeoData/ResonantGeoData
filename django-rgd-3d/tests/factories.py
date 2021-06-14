import factory
import factory.django
from rgd_3d import models
from rgd_testing_utils.factories import ChecksumFileFactory


class PointCloudFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PointCloudFile

    file = factory.SubFactory(ChecksumFileFactory)
