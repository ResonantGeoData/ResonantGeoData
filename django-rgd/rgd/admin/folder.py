from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.models import Folder


@admin.register(Folder)
class CollectionAdmin(OSMGeoAdmin):
    pass
