from django.contrib import admin
from django.db.models import FileField
from django.forms import TextInput
from django.template.defaultfilters import linebreaksbr
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django_admin_display import admin_display

from . import models
from . import tasks


def _text_preview(target_file: FileField, mimetype=None, show_end=True):
    """
    Return the text of a file if it is short or a portion of it if it is long.

    params:
        target_file: A FileField to read text from. (log or data file)
        mimetype: A string default to be 'None' for log (data file have a mimetype)
        show_end: A bool default to be True determines first/last portion for preview
    """
    # show log file preview while data file needs to be checked
    mimetype_check = mimetype is None or (mimetype is not None and mimetype.startswith('text/'))
    # if mimetype_check fails, no need to read files
    if not mimetype_check:
        return None
    # max file size for display, currently 10kb
    maxlen = 10000
    if target_file:
        with target_file.open('rb') as datafile:
            if len(datafile) > 0:
                if show_end:
                    # read and only display from the end for log filess
                    display_message = 'last'
                    # seek reference
                    datafile.seek(max(0, len(target_file) - maxlen))
                else:
                    # no need for seek reference if start with the beginning
                    display_message = 'first'
                message = datafile.read(maxlen).decode(errors='replace')
                if len(target_file) < maxlen:
                    return mark_safe('<PRE>' + escape(message) + '</PRE>')
                else:
                    prefix_message = f"""The output is too large to display in the browser.
                Only the {display_message} {maxlen} characters are displayed.
                """
                    prefix_message = linebreaksbr(prefix_message)
                    return mark_safe(prefix_message + '<PRE>' + escape(message) + '</PRE>')
            else:
                return 'File is empty'
    else:
        return 'No file provided'


def _link_url(name, obj, field):
    if not getattr(obj, field, None):
        return 'No attachment'
    url = getattr(obj, field).url
    if '//minio:' in url:
        url = '/api/download/%s/%s/%s' % (name, obj.id, field)
    return mark_safe('<a href="%s" download>Download</a>' % (url,))


@admin.register(models.Algorithm)
class AlgorithmAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'creator', 'created', 'active', 'data_link')
    readonly_fields = ('data_link',)

    def data_link(self, obj):
        return _link_url('algorithm', obj, 'data')

    data_link.allow_tags = True

    # overrride default textfield model
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'docker_image_id':
            formfield.widget = TextInput(attrs=formfield.widget.attrs)
        return formfield


@admin.register(models.AlgorithmJob)
class AlgorithmJobAdmin(admin.ModelAdmin):
    @admin_display(short_description='Run algorithm')
    def run_algorithm(self, request, queryset):
        for algorithm_job in queryset:
            tasks.run_algorithm.delay(algorithm_job.id)

    list_display = ('__str__', 'creator', 'created', 'algorithm', 'dataset', 'status')
    actions = [run_algorithm]


@admin.register(models.AlgorithmResult)
class AlgorithmResultAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'created',
        'algorithm_job',
        'algorithm',
        'dataset',
        'data_link',
        'log_link',
    )
    readonly_fields = ('data_link', 'algorithm', 'dataset', 'log_link', 'log_preview')

    # override readonly_fields to hide result_preview if no result or mimetype not 'text'
    def get_readonly_fields(self, request, obj):
        result = _text_preview(obj.data, obj.data_mimetype, False)
        if result is None:
            readonly_fields = ('data_link', 'algorithm', 'dataset', 'log_link', 'log_preview')
        else:
            readonly_fields = (
                'data_link',
                'algorithm',
                'dataset',
                'log_link',
                'log_preview',
                'result_preview',
            )
        return readonly_fields

    def data_link(self, obj):
        return _link_url('algorithm_result', obj, 'data')

    data_link.allow_tags = True

    def log_link(self, obj):
        return _link_url('algorithm_result', obj, 'log')

    log_link.allow_tags = True

    def algorithm(self, obj):
        return obj.algorithm_job.algorithm

    def dataset(self, obj):
        return obj.algorithm_job.dataset

    def log_preview(self, obj):
        return _text_preview(obj.log)

    def result_preview(self, obj):
        return _text_preview(obj.data, obj.data_mimetype, False)

    # overrride default textfield model from textarea to text input
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'data_mimetype':
            formfield.widget = TextInput(attrs=formfield.widget.attrs)
        return formfield


@admin.register(models.Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'creator', 'created', 'task_list', 'active', 'data_link')
    readonly_fields = ('data_link', 'task_list')

    def data_link(self, obj):
        return _link_url('dataset', obj, 'data')

    data_link.allow_tags = True

    def task_list(self, obj):
        return ', '.join([t.name for t in obj.tasks.all()])


@admin.register(models.Groundtruth)
class GroundtruthAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'task', 'creator', 'created', 'active', 'public', 'data_link')
    readonly_fields = ('data_link',)

    def data_link(self, obj):
        return _link_url('groundtruth', obj, 'data')

    data_link.allow_tags = True


@admin.register(models.ScoreAlgorithm)
# subclassing AlgorithmAdmin to avoid duplicate codes
class ScoreAlgorithmAdmin(AlgorithmAdmin):
    list_display = ('__str__', 'task', 'creator', 'created', 'active', 'data_link')


@admin.register(models.ScoreJob)
class ScoreJobAdmin(admin.ModelAdmin):
    @admin_display(short_description='Run scoring')
    def run_scoring(self, request, queryset):
        for score_job in queryset:
            tasks.run_scoring.delay(score_job.id)

    list_display = (
        '__str__',
        'creator',
        'created',
        'score_algorithm',
        'algorithm_result',
        'groundtruth',
        'status',
    )
    actions = [run_scoring]


@admin.register(models.ScoreResult)
class ScoreResultAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'created',
        'score_job',
        'algorithm',
        'dataset',
        'algorithm_result',
        'score_algorithm',
        'groundtruth',
        'data_link',
        'log_link',
        'overall_score',
        'result_type',
    )
    readonly_fields = (
        'data_link',
        'log_link',
        'algorithm',
        'dataset',
        'algorithm_result',
        'score_algorithm',
        'groundtruth',
        'overall_score',
        'result_type',
        'log_preview',
    )

    def data_link(self, obj):
        return _link_url('score_result', obj, 'data')

    data_link.allow_tags = True

    def log_link(self, obj):
        return _link_url('score_result', obj, 'log')

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
        return _text_preview(obj.log)


@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'creator', 'created', 'active')
