from django.contrib.auth.models import User
import factory
import factory.django

from geodata import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user_%d' % n)
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


# @register
# class DatasetFactory(factory.django.DjangoModelFactory):
#     class Meta:
#         model = models.Dataset
#
#     name = factory.Faker('sentence', nb_words=2)
#     description = factory.Faker('paragraph')


class ImageFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ImageFile

    name = factory.Faker('sentence', nb_words=2)
    file = factory.django.FileField(filename='sample.dat')
    compute_checksum = True
    # creator = factory.SubFactory(UserFactory)
    # modifier = factory.SubFactory(UserFactory)


class RasterEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.RasterEntry

    name = factory.Faker('sentence', nb_words=2)

    @factory.post_generation
    def images(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for image in extracted:
                self.images.add(image)

    # If we have an on_commit or post_save method that modifies the model, we
    # need to refresh it afterwards.
    @classmethod
    def _after_postgeneration(cls, instance, *args, **kwargs):
        super()._after_postgeneration(instance, *args, **kwargs)
        instance.refresh_from_db()


# TODO: add "geometries" and "rasters"
# https://factoryboy.readthedocs.io/en/latest/recipes.html#simple-many-to-many-relationship


# For generating lat-lon coords, this may be helpful:
# https://faker.readthedocs.io/en/latest/providers/faker.providers.geo.html
