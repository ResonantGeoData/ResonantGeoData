import inspect

from django.conf.urls import include
from django.contrib import admin
from django.contrib.gis.db import models as base_models
from django.urls import path
from djproxy.urls import generate_routes
from rest_framework.routers import SimpleRouter

from . import models
from . import views
from rgd import utility


router = SimpleRouter()
for model_name, model in inspect.getmembers(models):
    if inspect.isclass(model):
        if (model.__bases__[0] == base_models.Model):
            serializer_class = utility.create_serializer(model)
            viewset_class = utility.create_viewset(serializer_class)
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
    path('api/core/download/<model>/<int:id>/<field>', views.download_file, name='download-file'),
    path('', include(router.urls)),
] + generate_routes({'flower-proxy': {'base_url': 'http://flower:5555/', 'prefix': '/flower/'}})

handler500 = views.handler500
