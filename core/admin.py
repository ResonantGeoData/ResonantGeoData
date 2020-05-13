from django.contrib import admin
from django_admin_display import admin_display
from django.utils.safestring import mark_safe
import os

from . import models
from . import tasks


# should take the FileField object rather than the model.
# a module for log preview
def _text_preview(log_file):
    # max file size for display, currently 100kb
    maxlen = 10000
    prefix_message = 'The output is too large to display in the browser.\n'
    prefix_message += ('Only the last %s characters are displayed.\n \n' % (maxlen))
    if log_file:
        with log_file.open('rb') as datafile:
            if len(datafile) > 0:
                try:
                    datafile.seek(-maxlen, os.SEEK_END)
                except OSError as exc:
                    if exc.errno != 22:
                        # reraise exceptions except for trying to seek before the beginning
                        raise
                message = datafile.read().decode(errors='replace')
                if len(log_file) < maxlen:
                    # different prefix depends on the output size?
                    prefix_message = 'Log output: \n'
                    return prefix_message + message
                else:
                    return prefix_message + message
            else:
                return 'Log is empty'
    else:
        return 'No log file to display'


@admin_display(short_description='Run algorithm')
def run_algorithm(modeladmin, request, queryset):
    for algorithm_job in queryset:
        tasks.run_algorithm.delay(algorithm_job.id)


@admin_display(short_description='Run scoring')
def run_scoring(modeladmin, request, queryset):
    for score_job in queryset:
        tasks.run_scoring.delay(score_job.id)


@admin.register(models.Algorithm)
class AlgorithmAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'creator', 'created', 'active', 'data_link')
    readonly_fields = ('data_link',)

    def data_link(self, obj):
        if obj.data:
            return mark_safe('<a href="%s" download>Download</a>' % (obj.data.url,))
        else:
            return 'No attachment'

    data_link.allow_tags = True


@admin.register(models.AlgorithmJob)
class AlgorithmJobAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'creator', 'created', 'algorithm', 'dataset', 'status')
    actions = [run_algorithm]


@admin.register(models.AlgorithmResult)
class AlgorithmResultAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created', 'algorithm_job', 'algorithm', 'dataset', 'data_link', 'log_link')
    readonly_fields = ('data_link', 'algorithm', 'dataset', 'log_link', 'log_preview')

    def data_link(self, obj):
        if obj.data:
            return mark_safe('<a href="%s" download>Download</a>' % (obj.data.url,))
        else:
            return 'No attachment'

    data_link.allow_tags = True

    def log_link(self, obj):
        if obj.log:
            return mark_safe('<a href="%s" download>Download</a>' % (obj.log.url,))
        else:
            return 'No attachment'

    log_link.allow_tags = True

    def algorithm(self, obj):
        return obj.algorithm_job.algorithm

    def dataset(self, obj):
        return obj.algorithm_job.dataset

    def log_preview(self, obj):
        return _text_preview(obj.log)


@admin.register(models.Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'creator', 'created', 'task_list', 'active', 'data_link')
    readonly_fields = ('data_link', 'task_list')

    def data_link(self, obj):
        if obj.data:
            return mark_safe('<a href="%s" download>Download</a>' % (obj.data.url,))
        else:
            return 'No attachment'

    data_link.allow_tags = True

    def task_list(self, obj):
        return ', '.join([t.name for t in obj.tasks.all()])


@admin.register(models.Groundtruth)
class GroundtruthAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'task', 'creator', 'created', 'active', 'public', 'data_link')
    readonly_fields = ('data_link',)

    def data_link(self, obj):
        if obj.data:
            return mark_safe('<a href="%s" download>Download</a>' % (obj.data.url,))
        else:
            return 'No attachment'

    data_link.allow_tags = True


@admin.register(models.ScoreAlgorithm)
class ScoreAlgorithmAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'task', 'creator', 'created', 'active', 'data_link')
    readonly_fields = ('data_link',)

    def data_link(self, obj):
        if obj.data:
            return mark_safe('<a href="%s" download>Download</a>' % (obj.data.url,))
        else:
            return 'No attachment'

    data_link.allow_tags = True


@admin.register(models.ScoreJob)
class ScoreJobAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'creator', 'created', 'score_algorithm', 'algorithm_result', 'groundtruth', 'status')
    actions = [run_scoring]


@admin.register(models.ScoreResult)
class ScoreResultAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'created', 'score_job', 'algorithm', 'dataset', 'algorithm_result',
        'score_algorithm', 'groundtruth', 'data_link', 'log_link', 'overall_score', 'result_type')
    readonly_fields = (
        'data_link', 'log_link', 'algorithm', 'dataset', 'algorithm_result',
        'score_algorithm', 'groundtruth', 'overall_score', 'result_type', 'log_preview')

    def data_link(self, obj):
        if obj.data:
            return mark_safe('<a href="%s" download>Download</a>' % (obj.data.url,))
        else:
            return 'No attachment'

    data_link.allow_tags = True

    def log_link(self, obj):
        if obj.log:
            return mark_safe('<a href="%s" download>Download</a>' % (obj.log.url,))
        else:
            return 'No attachment'

    log_link.allow_tags = True

    def algorithm(self, obj):
        return obj.score_job.algorithm_result.algorithm_job.algorithm

    def dataset(self, obj):
        return obj.score_job.algorithm_result.algorithm_job.dataset

    def algorithm_result(self, obj):
        return obj.score_job.algorithm_result

    def score_algorithm(self, obj):
        return obj.score_job.score_algorithm

    def groundtruth(self, obj):
        return obj.score_job.groundtruth

    def overall_score(self, obj):
        return obj.score_job.overall_score

    def result_type(self, obj):
        return obj.score_job.result_type

    def log_preview(self, obj):
        return _text_preview(obj.log)


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'creator', 'created', 'active')
