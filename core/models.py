from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone


# We may want to have some sort of access permissions on Task, Dataset,
# Groundtruth, etc.


class Task(models.Model):
    def __str__(self):
        return f'Task ({self.id}) {self.name}'

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(get_user_model(), on_delete=models.DO_NOTHING)
    created = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)


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
    # TODO: If we try to edit data and this has been referenced anywhere, we
    # need to make a new model and mark this one as inactive
    data = models.FileField(upload_to='algorithm')


class AlgorithmResult(models.Model):
    algorithm = models.ForeignKey(Algorithm, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)
    # TODO: if results are small, do we want to store them in the database?
    data = models.FileField(upload_to='results')


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
    # TODO: If we try to edit data and this has been referenced anywhere, we
    # need to make a new model and mark this one as inactive
    data = models.FileField(upload_to='scorealgorithm')


class ScoreResult(models.Model):
    algorithmresult = models.ForeignKey(AlgorithmResult, on_delete=models.CASCADE)
    groundtruth = models.ForeignKey(Groundtruth, on_delete=models.CASCADE)
    scorealgorithm = models.ForeignKey(ScoreAlgorithm, on_delete=models.CASCADE)
    created = models.DateTimeField(default=timezone.now)
    # TODO: if results are small, do we want to store them in the database?
    data = models.FileField(upload_to='scores')
