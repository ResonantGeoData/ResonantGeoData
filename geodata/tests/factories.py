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


class GeometryArchiveFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.GeometryArchive

    name = factory.Faker('sentence', nb_words=2)
    file = factory.django.FileField(filename='sample.dat')
    compute_checksum = True


class ArbitraryFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ArbitraryFile

    file = factory.django.FileField(filename='sample.dat')


class KWCOCOArchiveFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.KWCOCOArchive

    name = factory.Faker('sentence', nb_words=2)
    spec_file = factory.SubFactory(ArbitraryFileFactory)
    image_archive = factory.SubFactory(ArbitraryFileFactory)

    # If we have an on_commit or post_save method that modifies the model, we
    # need to refresh it afterwards.
    @classmethod
    def _after_postgeneration(cls, instance, *args, **kwargs):
        super()._after_postgeneration(instance, *args, **kwargs)
        instance.refresh_from_db()


class FMVFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FMVFile

    name = factory.Faker('sentence', nb_words=2)
    file = factory.django.FileField(filename='sample.mpeg')

    # If we have an on_commit or post_save method that modifies the model, we
    # need to refresh it afterwards.
    @classmethod
    def _after_postgeneration(cls, instance, *args, **kwargs):
        super()._after_postgeneration(instance, *args, **kwargs)
        instance.refresh_from_db()


class FMVEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FMVEntry

    name = factory.Faker('sentence', nb_words=2)
    # fmv_file = factory.SubFactory(FMVFileFactory)
    klv_file = factory.django.FileField(filename='sample.klv')
    web_video_file = factory.django.FileField(filename='sample.mp4')


# https://factoryboy.readthedocs.io/en/latest/recipes.html#simple-many-to-many-relationship
# For generating lat-lon coords, this may be helpful:
# https://faker.readthedocs.io/en/latest/providers/faker.providers.geo.html
