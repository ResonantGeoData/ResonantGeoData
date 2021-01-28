from django.contrib.auth.models import User
import factory
import factory.django

from rgd.geodata import models


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: 'user_%d' % n)
    email = factory.Faker('safe_email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')


class ChecksumFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ChecksumFile

    file = factory.django.FileField(filename='sample.dat')

    # If we have an on_commit or post_save method that modifies the model, we
    # need to refresh it afterwards.
    @classmethod
    def _after_postgeneration(cls, instance, *args, **kwargs):
        super()._after_postgeneration(instance, *args, **kwargs)
        instance.refresh_from_db()


class ImageFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ImageFile

    file = factory.SubFactory(ChecksumFileFactory)
    # creator = factory.SubFactory(UserFactory)
    # modifier = factory.SubFactory(UserFactory)


class ImageSetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ImageSet

    name = factory.Faker('sentence', nb_words=2)

    @factory.post_generation
    def images(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for image in extracted:
                self.images.add(image)


class RasterEntryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.RasterEntry

    name = factory.Faker('sentence', nb_words=2)
    image_set = factory.SubFactory(ImageSetFactory)

    # If we have an on_commit or post_save method that modifies the model, we
    # need to refresh it afterwards.
    @classmethod
    def _after_postgeneration(cls, instance, *args, **kwargs):
        super()._after_postgeneration(instance, *args, **kwargs)
        instance.refresh_from_db()


class GeometryArchiveFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.GeometryArchive

    file = factory.SubFactory(ChecksumFileFactory)


class KWCOCOArchiveFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.KWCOCOArchive

    name = factory.Faker('sentence', nb_words=2)
    spec_file = factory.SubFactory(ChecksumFileFactory)
    image_archive = factory.SubFactory(ChecksumFileFactory)

    # If we have an on_commit or post_save method that modifies the model, we
    # need to refresh it afterwards.
    @classmethod
    def _after_postgeneration(cls, instance, *args, **kwargs):
        super()._after_postgeneration(instance, *args, **kwargs)
        instance.refresh_from_db()


class FMVFileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FMVFile

    file = factory.SubFactory(ChecksumFileFactory)
    klv_file = factory.django.FileField(filename='sample.klv')
    web_video_file = factory.django.FileField(filename='sample.mp4')
    frame_rate = 30

    # If we have an on_commit or post_save method that modifies the model, we
    # need to refresh it afterwards.
    @classmethod
    def _after_postgeneration(cls, instance, *args, **kwargs):
        super()._after_postgeneration(instance, *args, **kwargs)
        instance.refresh_from_db()


# https://factoryboy.readthedocs.io/en/latest/recipes.html#simple-many-to-many-relationship
# For generating lat-lon coords, this may be helpful:
# https://faker.readthedocs.io/en/latest/providers/faker.providers.geo.html
