from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.models import ChecksumFile, FileSet

from .mixins import MODIFIABLE_FILTERS


class ChecksumFileInline(admin.TabularInline):
    model = ChecksumFile
    fk_name = 'file_set'
    # fields = ()
    extra = 0


@admin.register(FileSet)
class FileSetAdmin(OSMGeoAdmin):
    list_display = [
        'name',
        'collection',
    ]
    list_filter = MODIFIABLE_FILTERS + ('collection',)
