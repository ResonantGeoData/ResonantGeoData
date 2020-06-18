from django.conf.urls import include
from django.contrib import admin
from django.urls import path
from djproxy.urls import generate_routes
from rest_framework.routers import SimpleRouter

from . import views


router = SimpleRouter()
router.register('api/algorithms', views.AlgorithmViewSet)
router.register('api/tasks', views.TaskViewSet)
router.register('api/dataset', views.DatasetViewSet)
router.register('api/groundtruth', views.GroundtruthViewSet)
router.register('api/score_algorithm', views.ScoreAlgorithmViewSet)
router.register('api/algorithm_job', views.AlgorithmJobViewSet)
router.register('api/algorithm_result', views.AlgorithmResultViewSet)
router.register('api/score_job', views.ScoreJobViewSet)
router.register('api/score_result', views.ScoreResultViewSet)


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
