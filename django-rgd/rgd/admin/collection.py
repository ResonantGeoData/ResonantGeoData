from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin
from rgd.models import Collection, CollectionPermission


class CollectionPermissionInline(admin.TabularInline):
    model = CollectionPermission
    fk_name = 'collection'
    fields = ('user', 'role')
    extra = 1


@admin.register(Collection)
class CollectionAdmin(OSMGeoAdmin):
    fields = ('name',)
    inlines = (CollectionPermissionInline,)
