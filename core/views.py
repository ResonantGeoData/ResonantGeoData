from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
import logging

from .models import AlgorithmJob, Task


logger = logging.getLogger(__name__)


def handler500(request):
    return render(request, 'errors/application-error.html', status=500)


def index(request):
    context = {
        'tasks': Task.objects.all(),
    }
    return render(request, 'index.html', context)


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
    context = {

    }
    return render(request, 'core/algorithms.html', )#context)


@login_required
def jobs(request):
    """Dashboard of a user's jobs."""
    context = {

    }
    return render(request, 'core/jobs.html', )#context)


@login_required
def tasks(request):
    """All task postings."""
    context = {

    }
    return render(request, 'core/tasks.html', )#context)
