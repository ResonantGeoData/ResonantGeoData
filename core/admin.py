from django.contrib import admin

from . import models


admin.site.register(models.Task)
admin.site.register(models.Dataset)
admin.site.register(models.Groundtruth)
admin.site.register(models.Algorithm)
admin.site.register(models.AlgorithmResult)
admin.site.register(models.ScoreAlgorithm)
admin.site.register(models.ScoreResult)
