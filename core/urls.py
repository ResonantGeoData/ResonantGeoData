import inspect

from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from django_filters.rest_framework import DjangoFilterBackend
from djproxy.urls import generate_routes
from rest_framework import viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.routers import SimpleRouter

from . import serializers
from . import views


router = SimpleRouter()
for _, ser in inspect.getmembers(serializers):
    if inspect.isclass(ser):
        model = ser.Meta.model
        model_name = model.__name__
        viewsetClass = type(
            model_name + 'ViewSet',
            (viewsets.ModelViewSet,),
            {
                'parser_classes': (MultiPartParser,),
                'queryset': model.objects.all(),
                'serializer_class': ser,
                'filter_backends': [DjangoFilterBackend],
                'filterset_fields': views.get_filter_fields(model),
            },
        )
        router.register('api/%s' % (model_name.lower()), viewsetClass)

admin.site.index_template = 'admin/add_flower.html'
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
