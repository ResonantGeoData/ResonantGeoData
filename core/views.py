import logging
import os

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models.fields import AutoField
from django.db.models.fields.files import FieldFile, FileField
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.encoding import smart_str
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DeleteView, DetailView
from rest_framework.decorators import api_view

from . import models
from .models import Algorithm, AlgorithmJob, ScoreJob, Task


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
    if not isinstance(getattr(model_inst, field, None), FieldFile):
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
