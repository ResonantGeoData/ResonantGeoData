from allauth.account.signals import user_signed_up
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from rgd import models
from rgd.utility import skip_signal


@receiver(post_save, sender=models.ChecksumFile)
@skip_signal()
def _post_save_checksum_file(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save_event_task(*args, **kwargs))


@receiver(user_signed_up)
def set_new_user_inactive(sender, **kwargs):
    user = kwargs.get('user')
    try:
        models.WhitelistedEmail.objects.get(email=user.email)
        user.is_active = True
    except models.WhitelistedEmail.DoesNotExist:
        user.is_active = False
    user.save(update_fields=['is_active'])
