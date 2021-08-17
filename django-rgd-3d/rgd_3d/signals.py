from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from rgd.utility import skip_signal
from rgd_3d import models


@receiver(post_save, sender=models.PointCloud)
@skip_signal()
def _post_save_point_cloud_file(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))


@receiver(post_save, sender=models.GRIB)
@skip_signal()
def _post_save_grib_file(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))


@receiver(post_delete, sender=models.GRIB)
@skip_signal()
def _post_delete_grib_file(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_delete(*args, **kwargs))
