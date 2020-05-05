from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

# We may want to have some sort of access permissions on Task, Dataset,
# Groundtruth, etc.

class DeferredFieldsManager(models.Manager):
    def __init__(self, *deferred_fields):
        self.deferred_fields = deferred_fields
        super().__init__()

    def get_queryset(self):
        return super().get_queryset().defer(*self.deferred_fields)


class Task(models.Model):
    def __str__(self):
        return f'Task ({self.id}) {self.name}'

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Dataset(models.Model):
    def __str__(self):
        return f'Dataset ({self.id}) {self.name}'

    # A tarball of data
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    tasks = models.ManyToManyField(Task)
    # TODO: If we try to edit data and this has been referenced anywhere, we
    # need to make a new model and mark this one as inactive
    data = models.FileField(upload_to='dataset')

    def __str__(self):
        return self.name


class Groundtruth(models.Model):
    # The data used by the scorer to compare the output of the algorithm
    def __str__(self):
        return f'Groundtruth ({self.id}) {self.name}'

    class Meta:
        """
        Groundtruth is for a specific task and dataset
        """
        unique_together = ('task', 'dataset')

    name = models.CharField(max_length=100)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    # public is True for test datasets, False for internal datasets
    public = models.BooleanField(default=False)
    # TODO: If we try to edit data and this has been referenced anywhere, we
    # need to make a new model and mark this one as inactive
    data = models.FileField(upload_to='groundtruth')

    def __str__(self):
        return self.name


class Algorithm(models.Model):
    def __str__(self):
        return f'Algorithm ({self.id}) {self.name}'

    # A docker that takes a dataset and outputs results
    # A docker tarball; when creating, we can offer to pull a docker
    name = models.CharField(max_length=100, unique=True)
    # TODO: allow for multiple tasks
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    docker_image_id = models.TextField(null=True, blank=True)
    # TODO: If we try to edit data and this has been referenced anywhere, we
    # need to make a new model and mark this one as inactive
    data = models.FileField(upload_to='algorithm')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('algorithm-detail', kwargs={'creator': str(self.creator), 'pk': self.pk})


class ScoreAlgorithm(models.Model):
    def __str__(self):
        return f'Score Algorithm ({self.id}) {self.name}'

    # A docker that takes an algorithm's output and a groundtruth as input and
    # outputs a score
    # A docker tarball; when creating, we can offer to pull a docker
    name = models.CharField(max_length=100, unique=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    docker_image_id = models.TextField(null=True, blank=True)
    # TODO: If we try to edit data and this has been referenced anywhere, we
    # need to make a new model and mark this one as inactive
    data = models.FileField(upload_to='score_algorithm')

    def __str__(self):
        return self.name


class AlgorithmJob(models.Model):
    class Meta:
        ordering = ['-created']

    class Status(models.TextChoices):
        QUEUED = 'queued', _('Queued for processing')
        RUNNING = 'running', _('Processing')
        INTERNAL_FAILURE = 'internal_failure', _('Internal failure')
        FAILED = 'failed', _('Failed')
        SUCCEEDED = 'success', _('Succeeded')

    algorithm = models.ForeignKey(Algorithm, on_delete=models.DO_NOTHING)
    dataset = models.ForeignKey(Dataset, on_delete=models.DO_NOTHING)
    creator = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default=Status.QUEUED, choices=Status.choices)
    fail_reason = models.TextField(blank=True)

    # it might be nice to have an array of status/timestamp/log for tracking
    # when status changed.

    def run_algorithm(self):
        from . import tasks

        tasks.run_algorithm(self)


class AlgorithmResult(models.Model):
    algorithm_job = models.ForeignKey(AlgorithmJob, on_delete=models.CASCADE, blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)
    data = models.FileField(upload_to='results')
    log = models.FileField(upload_to='results_logs', null=True, blank=True)


class ScoreJob(models.Model):
    class Status(models.TextChoices):
        QUEUED = 'queued', _('Queued for processing')
        RUNNING = 'running', _('Processing')
        INTERNAL_FAILURE = 'internal_failure', _('Internal failure')
        FAILED = 'failed', _('Failed')
        SUCCEEDED = 'success', _('Succeeded')

    score_algorithm = models.ForeignKey(ScoreAlgorithm, on_delete=models.DO_NOTHING)
    algorithm_result = models.ForeignKey(AlgorithmResult, on_delete=models.DO_NOTHING)
    groundtruth = models.ForeignKey(Groundtruth, on_delete=models.DO_NOTHING)
    creator = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, default=Status.QUEUED, choices=Status.choices)
    fail_reason = models.TextField(blank=True)

    # it might be nice to have an array of status/timestamp/log for tracking
    # when status changed.

    def run_scoring(self):
        from . import tasks

        tasks.run_scoring(self)


class ScoreResult(models.Model):
    score_job = models.ForeignKey(ScoreJob, on_delete=models.CASCADE, blank=True, null=True)
    created = models.DateTimeField(default=timezone.now)
    data = models.FileField(upload_to='scores')
    log = models.FileField(upload_to='scores_logs', null=True, blank=True)
