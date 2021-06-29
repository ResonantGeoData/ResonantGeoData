import factory
import factory.django
from rgd_geometry import models
from rgd_testing_utils.factories import ChecksumFileFactory


class GeometryArchiveFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.GeometryArchive

    file = factory.SubFactory(ChecksumFileFactory)
