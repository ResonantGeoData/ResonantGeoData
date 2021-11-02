from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.models import FileSet


@admin.register(FileSet)
class FileSetAdmin(OSMGeoAdmin):
    pass
