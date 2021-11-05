from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.models import FileSet

from .mixins import MODIFIABLE_FILTERS


@admin.register(FileSet)
class FileSetAdmin(OSMGeoAdmin):
    list_display = [
        'name',
    ]
    list_filter = MODIFIABLE_FILTERS
