import logging
import os
import re

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.fields.files import FieldFile, FileField
from django.db.models.fields import AutoField
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.encoding import smart_str
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, DetailView
from rest_framework.decorators import api_view

from . import models
from .models import Algorithm, AlgorithmJob, ScoreJob, Task, Dataset
from . import serializers

# from django.utils.decorators import method_decorator
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework.response import Response

from drf_yasg import openapi
from drf_yasg.app_settings import swagger_settings
from drf_yasg.inspectors import CoreAPICompatInspector, FieldInspector, NotHandled, SwaggerAutoSchema
from drf_yasg.utils import no_body, swagger_auto_schema


logger = logging.getLogger(__name__)


def handler500(request):
    return render(request, 'errors/application-error.html', status=500)


def index(request):
    return render(request, 'index.html')


@login_required
@require_http_methods(['POST'])
def run_algorithm(request, algorithm_job_id):
    algorithm_job = get_object_or_404(AlgorithmJob, pk=algorithm_job_id)
    algorithm_job.run_algorithm()


@login_required
@require_http_methods(['POST'])
def run_scoring(request, score_job_id):
    score_job = get_object_or_404(ScoreJob, pk=score_job_id)
    score_job.run_scoring()


@login_required
def algorithms(request):
    """Dashboard of user's uploaded algorithms."""
    # Get a list of all of the algorithms for the current user
    user = request.user
    # another way: models.Algorithm.objects.filter(creator=user)
    algs = user.algorithm_set.all()
    context = {
        'algorithms': algs,
    }
    return render(request, 'core/algorithms.html', context)


@login_required
def jobs(request):
    """Dashboard of a user's jobs."""
    user = request.user
    jobs = user.algorithmjob_set.all()
    context = {
        'jobs': jobs,
    }
    return render(request, 'core/jobs.html', context)


@login_required
def tasks(request):
    """All task postings."""
    context = {
        'tasks': Task.objects.all(),
    }
    return render(request, 'core/tasks.html', context)


class _CustomUserTest(UserPassesTestMixin):
    """A helper to ensure that the current user is only requesting a view their own data."""

    def test_func(self):
        object = self.get_object()
        return self.request.user == object.creator


class AlgorithmDetailView(LoginRequiredMixin, _CustomUserTest, DetailView):
    model = Algorithm


class AlgorithmDeleteView(LoginRequiredMixin, _CustomUserTest, DeleteView):
    model = Algorithm
    success_url = '/algorithms/'


class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task


class JobDetailView(LoginRequiredMixin, _CustomUserTest, DetailView):
    model = AlgorithmJob


class AlgorithmCreateView(LoginRequiredMixin, CreateView):
    model = Algorithm
    fields = ['name', 'task', 'description', 'data', 'active']

    def form_valid(self, form):
        form.instance.creator = self.request.user
        form.instance.created = timezone.now()
        return super().form_valid(form)


class JobCreateView(LoginRequiredMixin, CreateView):
    model = AlgorithmJob
    fields = [
        'algorithm',
        'dataset',
    ]

    def form_valid(self, form):
        form.instance.creator = self.request.user
        form.instance.created = timezone.now()
        return super().form_valid(form)


@api_view(['GET'])
def download_file(request, model, id, field):
    model_class = ''.join([part[:1].upper() + part[1:] for part in model.split('_')])
    if not hasattr(models, model_class):
        raise Exception('No such model (%s)' % model)
    model_inst = get_object_or_404(getattr(models, model_class), pk=id)
    if not isinstance(getattr(model_inst, field, None), FileField):
        raise Exception('No such file (%s)' % field)
    file = getattr(model_inst, field)
    filename = os.path.basename(file.name)
    if not filename:
        filename = '%s_%s_%s.dat' % (model, id, field)
    mimetype = getattr(
        model_inst,
        '%s_mimetype' % field,
        'text/plain' if field == 'log' else 'application/octet-stream',
    )
    response = HttpResponse(file.chunks(), content_type=mimetype)
    response['Content-Disposition'] = smart_str(u'attachment; filename=%s' % filename)
    if len(file) is not None:
        response['Content-Length'] = len(file)
    return response

def get_filter_fields(model):
    model_fields = model._meta.get_fields()
    fields = []
    for field in model_fields:
        # print(type(field))
        res = str(field).split('.')
        if res[1] == model.__name__ and not isinstance(field, FileField) and not isinstance(field, AutoField):
            fields.append(field.name)
    return fields


class AlgorithmViewSet(viewsets.ModelViewSet):
    queryset = Algorithm.objects.all()
    serializer_class = serializers.AlgorithmSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'task', 'description', 'creator', 'created', 'active']


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = serializers.TaskSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'description', 'creator', 'created', 'active']


class DatasetViewSet(viewsets.ModelViewSet):
    queryset = Dataset.objects.all()
    serializer_class = serializers.DatasetSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name', 'description', 'creator', 'created', 'active', 'tasks']

class GroundtruthViewSet(viewsets.ModelViewSet):
    queryset = models.Groundtruth.objects.all()
    serializer_class = serializers.GroundtruthSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = get_filter_fields(models.Groundtruth)

class ScoreAlgorithmViewSet(viewsets.ModelViewSet):
    queryset = models.ScoreAlgorithm.objects.all()
    serializer_class = serializers.ScoreAlgorithmSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = get_filter_fields(models.ScoreAlgorithm)

class AlgorithmJobViewSet(viewsets.ModelViewSet):
    queryset = models.AlgorithmJob.objects.all()
    serializer_class = serializers.AlgorithmJobSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = get_filter_fields(models.AlgorithmJob)

class AlgorithmResultViewSet(viewsets.ModelViewSet):
    queryset = models.AlgorithmResult.objects.all()
    serializer_class = serializers.AlgorithmResultSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = get_filter_fields(models.AlgorithmResult)

class ScoreJobViewSet(viewsets.ModelViewSet):
    queryset = models.ScoreJob.objects.all()
    serializer_class = serializers.ScoreJobSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = get_filter_fields(models.ScoreJob)

class ScoreResultViewSet(viewsets.ModelViewSet):
    queryset = models.ScoreResult.objects.all()
    serializer_class = serializers.ScoreResultSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = get_filter_fields(models.ScoreResult)