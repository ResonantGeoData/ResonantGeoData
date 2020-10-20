from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Algorithm, AlgorithmJob, ScoreAlgorithm, ScoreJob


@receiver(post_save, sender=Algorithm)
def _post_save_algorithm(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(**kwargs))


@receiver(post_save, sender=ScoreAlgorithm)
def _post_save_score_algorithm(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(**kwargs))


@receiver(post_save, sender=AlgorithmJob)
def _post_save_algorithm_job(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(**kwargs))


@receiver(post_save, sender=ScoreJob)
def _post_save_score_job(sender, instance, *args, **kwargs):
    transaction.on_commit(lambda: instance._post_save(**kwargs))
