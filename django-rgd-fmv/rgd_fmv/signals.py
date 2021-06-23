from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from rgd.utility import skip_signal
from rgd_fmv import models


@receiver(post_save, sender=models.FMV)
@skip_signal()
def _post_save_fmv_file(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))
