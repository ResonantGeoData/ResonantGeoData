from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (ListView, DetailView, CreateView, UpdateView,
                                  DeleteView,
                                  )
import logging

from .models import Algorithm, AlgorithmJob, Task


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
def run_scoring(request, algorithm_job_id):
    score_job = get_object_or_404(ScoreJob, pk=score_job_id)
    score_job.run_scoring()


@login_required
def algorithms(request):
    """Dashboard of user's uploaded algorithms."""
    ## Get a list of all of the algorithms for the current user
    user = request.user
    # another way: models.Algorithm.objects.filter(creator=user)
    algs = user.algorithm_set.all()
    context = {
        'algorithms' : algs,
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
    """A helper to ensure that the current user is only requesting o view their own data."""

    def test_func(self):
        object = self.get_object()
        return self.request.user == object.creator


class AlgorithmDetailView(_CustomUserTest, DetailView):
    model = Algorithm


class AlgorithmCreateView(LoginRequiredMixin, CreateView):
    model = Algorithm
    fields = ['name', 'task', 'description', 'data', 'active']

    def form_valid(self, form):
        form.instance.creator = self.request.user
        form.instance.created = timezone.now()
        return super().form_valid(form)
