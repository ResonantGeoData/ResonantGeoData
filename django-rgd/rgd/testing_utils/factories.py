import factory
import factory.django
from rgd import models


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
