import copy

from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

MODIFIABLE_FILTERS = (
    'modified',
    'created',
)

SPATIAL_ENTRY_FILTERS = (
    'acquisition_date',
    'instrumentation',
)

TASK_EVENT_FILTERS = ('status',)

TASK_EVENT_READONLY = (
    'failure_reason',
    'status',
)


class _FileGetNameMixin:
    def get_name(self, obj):
        return obj.file.name

    get_name.short_description = 'Name'
    get_name.admin_order_field = 'file__name'


def reprocess(modeladmin, request, queryset):
    """Trigger the save event task for each entry."""
    for entry in queryset.all():
        entry.save()


class GeoAdminInline(OSMGeoAdmin, admin.StackedInline):
    def __init__(self, parent_model, admin_site):
        self.admin_site = admin_site
        self.parent_model = parent_model
        self.opts = self.model._meta
        self.has_registered_model = admin_site.is_registered(self.model)
        overrides = copy.deepcopy(admin.options.FORMFIELD_FOR_DBFIELD_DEFAULTS)
        for k, v in self.formfield_overrides.items():
            overrides.setdefault(k, {}).update(v)
        self.formfield_overrides = overrides
        if self.verbose_name is None:
            self.verbose_name = self.model._meta.verbose_name
        if self.verbose_name_plural is None:
            self.verbose_name_plural = self.model._meta.verbose_name_plural
