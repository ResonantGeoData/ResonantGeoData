import inspect

from django.conf.urls import include
from django.contrib import admin
from django.db.models import fields
from django.http import QueryDict
from django.urls import path
from django_filters.rest_framework import DjangoFilterBackend
from djproxy.urls import generate_routes
from rest_framework import parsers, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.routers import SimpleRouter

from . import serializers
from . import views


class MultiPartJsonParser(MultiPartParser):
    def parse(self, stream, media_type=None, parser_context=None):
        result = super().parse(stream, media_type=media_type, parser_context=parser_context)

        data = {}
        arrays = {}

        model = None
        if parser_context and 'view' in parser_context:
            model = parser_context['view'].get_serializer_class().Meta.model
        for key, value in result.data.items():
            """
                Handle ManytoMany field data, parses lists of comma-separated integers that might be quoted.
                eg. "1,2"
            """
            if hasattr(model, key) and isinstance(
                getattr(model, key), fields.related_descriptors.ManyToManyDescriptor
            ):
                print(value)
                vals = value.replace('"', '')
                arrays[key] = [x for x in vals.split(',')]
            else:
                data[key] = value

        print(data)
        print(arrays)
        qdict = QueryDict('', mutable=True)
        qdict.update(data)

        for key in arrays:
            for val in arrays[key]:
                qdict.update({key: val})

        return parsers.DataAndFiles(qdict, result.files)


router = SimpleRouter()
for _, ser in inspect.getmembers(serializers):
    if inspect.isclass(ser):
        model = ser.Meta.model
        model_name = model.__name__
        viewset_class = type(
            model_name + 'ViewSet',
            (viewsets.ModelViewSet,),
            {
                'parser_classes': (MultiPartJsonParser,),
                'queryset': model.objects.all(),
                'serializer_class': ser,
                'filter_backends': [DjangoFilterBackend],
                'filterset_fields': views.get_filter_fields(model),
            },
        )
        router.register('api/%s' % (model_name.lower()), viewset_class)

admin.site.index_template = 'admin/add_links.html'
urlpatterns = [
    path('', views.index, name='index'),
    path('algorithms/', views.algorithms, name='algorithms'),
    path(
        'algorithms/<str:creator>/<int:pk>/',
        views.AlgorithmDetailView.as_view(),
        name='algorithm-detail',
    ),
    path(
        'algorithms/<str:creator>/<int:pk>/delete/',
        views.AlgorithmDeleteView.as_view(),
        name='delete-algorithm',
    ),
    path('algorithms/new/', views.AlgorithmCreateView.as_view(), name='new-algorithm'),
    path('jobs/', views.jobs, name='jobs'),
    path('jobs/new/', views.JobCreateView.as_view(), name='new-job'),
    path('jobs/<str:creator>/<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
    path('tasks/', views.tasks, name='tasks'),
    path('task/<int:pk>-<str:name>/', views.TaskDetailView.as_view(), name='task-detail'),
    path('api/download/<model>/<int:id>/<field>', views.download_file, name='download-file'),
    path('', include(router.urls)),
] + generate_routes({'flower-proxy': {'base_url': 'http://flower:5555/', 'prefix': '/flower/'}})

handler500 = views.handler500
