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
