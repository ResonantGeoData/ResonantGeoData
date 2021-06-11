import factory
import factory.django
from rgd.testing_utils.factories import ChecksumFileFactory
from rgd_fmv import models


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
