from django.contrib import admin
from django_admin_display import admin_display
from django.utils.safestring import mark_safe

from . import models
from . import tasks


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
    readonly_fields = ('data_link', 'algorithm', 'dataset', 'log_link', 'log_preview', 'log_message')

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
        return obj.algorithm_job.log_preview

    def log_message(self, obj):
        return obj.algorithm_job.log_message



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
        'score_algorithm', 'groundtruth', 'overall_score', 'result_type', 'log_preview', 'log_message')

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
        return obj.score_job.log_preview

    def log_message(self, obj):
        return obj.score_job.log_message


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'creator', 'created', 'active')
