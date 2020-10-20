import os

from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver

from .models.fmv import FMVFile
from .models.geometry import GeometryArchive
from .models.imagery import ImageFile, ImageSet, KWCOCOArchive, RasterEntry


@receiver(post_save, sender=FMVFile)
def _post_save_fmv_file(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))


@receiver(post_save, sender=GeometryArchive)
def _post_save_geometry_archive(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))


@receiver(m2m_changed, sender=ImageSet.images.through)
def _m2m_changed_image_set(sender, instance, action, reverse, *args, **kwargs):
    # If no name was specified for an ImageSet, when images are added to it,
    # use the common base name of all images as the name of the ImageSet.
    if action == 'post_add' and not instance.name and instance.images.count():
        names = [image.name for image in instance.images.all() if image.name]
        if len(names):
            instance.name = os.path.commonprefix(names)
            instance.save(update_fields=['name'])


@receiver(post_save, sender=RasterEntry)
def _post_save_raster_entry(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._on_commit_event_task(*args, **kwargs))


@receiver(post_save, sender=KWCOCOArchive)
def _post_save_kwcoco_dataset(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._on_commit_event_task(*args, **kwargs))


@receiver(post_delete, sender=KWCOCOArchive)
def _post_delete_kwcoco_dataset(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_delete(*args, **kwargs))


@receiver(post_save, sender=ImageFile)
def _post_save_image_file(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))
