from django.contrib.auth.models import User
import factory.django
from pytest_factoryboy import register

from geodata import models


@register
class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user_%d' % n)
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


@register
class DatasetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Dataset

    name = factory.Faker('sentence', nb_words=2)
    description = factory.Faker('paragraph')

    # TODO: add "geometries" and "rasters"
    # https://factoryboy.readthedocs.io/en/latest/recipes.html#simple-many-to-many-relationship


# For generating lat-lon coords, this may be helpful:
# https://faker.readthedocs.io/en/latest/providers/faker.providers.geo.html
