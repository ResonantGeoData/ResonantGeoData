import factory
import factory.django

from rgd_testing_utils.factories import ChecksumFileFactory

from rgd_imagery import models


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
