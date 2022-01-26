import os

from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver
from rgd.utility import skip_signal
from rgd_imagery import models


@receiver(m2m_changed, sender=models.ImageSet.images.through)
@skip_signal()
def _m2m_changed_image_set(sender, instance, action, reverse, *args, **kwargs):
    # If no name was specified for an ImageSet, when images are added to it,
    # use the common base name of all images as the name of the ImageSet.
    if action == 'post_add' and not instance.name and instance.images.count():
        names = [image.file.name for image in instance.images.all() if image.file.name]
        if len(names):
            instance.name = os.path.commonprefix(names)
            instance.save(update_fields=['name'])


@receiver(post_save, sender=models.Raster)
@skip_signal()
def _post_save_raster(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._on_commit_event_task(*args, **kwargs))


@receiver(post_save, sender=models.Image)
@skip_signal()
def _post_save_image_file(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))


@receiver(post_save, sender=models.ProcessedImage)
@skip_signal()
def _post_save_processed_image(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))


@receiver(pre_delete, sender=models.ProcessedImage)
@skip_signal()
def _pre_delete_processed_image(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._pre_delete(*args, **kwargs))


@receiver(post_save, sender=models.ProcessedImageGroup)
@skip_signal()
def _post_save_processed_image_group(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(*args, **kwargs))
