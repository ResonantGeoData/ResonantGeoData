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
            # Neither of these lines should be necessary.  It looks like in the
            # test environment, the footprint is computed but then clobbered by
            # (possibly) the complete save of the RasterEntry model that
            # initiated the computation of the footprint.  For now, retrigger
            # the process and refresh the model.
            self._pre_save_event_task()
            self.refresh_from_db()


# TODO: add "geometries" and "rasters"
# https://factoryboy.readthedocs.io/en/latest/recipes.html#simple-many-to-many-relationship


# For generating lat-lon coords, this may be helpful:
# https://faker.readthedocs.io/en/latest/providers/faker.providers.geo.html
