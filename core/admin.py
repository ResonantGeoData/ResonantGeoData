from django.contrib import admin
from django_admin_display import admin_display

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


class AlgorithmJobAdmin(admin.ModelAdmin):
    actions = [run_algorithm]


class ScoreJobAdmin(admin.ModelAdmin):
    actions = [run_scoring]


admin.site.register(models.Task)
admin.site.register(models.Dataset)
admin.site.register(models.Groundtruth)
admin.site.register(models.Algorithm)
admin.site.register(models.AlgorithmResult)
admin.site.register(models.ScoreAlgorithm)
admin.site.register(models.ScoreResult)
admin.site.register(models.AlgorithmJob, AlgorithmJobAdmin)
admin.site.register(models.ScoreJob, ScoreJobAdmin)
