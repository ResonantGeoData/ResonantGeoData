import factory
import factory.django
from rgd.testing_utils.factories import ChecksumFileFactory
from rgd_geometry import models


class GeometryArchiveFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.GeometryArchive

    file = factory.SubFactory(ChecksumFileFactory)
