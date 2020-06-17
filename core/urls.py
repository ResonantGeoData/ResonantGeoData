from django.contrib import admin
from django.urls import path
from djproxy.urls import generate_routes

from . import views

from django.conf.urls import include
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register('algorithms_api', views.AlgorithmViewSet)
router.register('tasks_api', views.TaskViewSet)
router.register('dataset_api', views.DatasetViewSet)
router.register('groundtruth_api', views.GroundtruthViewSet)
router.register('score_algorithm_api', views.ScoreAlgorithmViewSet)
router.register('algorithm_job_api', views.AlgorithmJobViewSet)
router.register('algorithm_result_api', views.AlgorithmResultViewSet)
router.register('score_job_api', views.ScoreJobViewSet)
router.register('score_result_api', views.ScoreResultViewSet)


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
    # path('', algorithm_list, name='algorithm_list'),
    path('', include(router.urls)),
] + generate_routes({'flower-proxy': {'base_url': 'http://flower:5555/', 'prefix': '/flower/'}})

handler500 = views.handler500
