import factory
import factory.django
from rgd_3d import models
from rgd_testing_utils.factories import ChecksumFileFactory


class Mesh3DFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Mesh3D

    file = factory.SubFactory(ChecksumFileFactory)
