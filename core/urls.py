from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('algorithms/', views.algorithms, name='algorithms'),
    path('algorithms/<str:creator>/<int:pk>/', views.AlgorithmDetailView.as_view(), name="algorithm-detail"),
    path('algorithms/<str:creator>/<int:pk>/delete/', views.AlgorithmDeleteView.as_view(), name="delete-algorithm"),
    path('algorithms/new/', views.AlgorithmCreateView.as_view(), name="new-algorithm"),
    path('jobs/', views.jobs, name='jobs'),
    path('jobs/new/', views.JobCreateView.as_view(), name="new-job"),
    path('jobs/<str:creator>/<int:pk>/', views.JobDetailView.as_view(), name="job-detail"),
    path('tasks/', views.tasks, name='tasks'),
    path('task/<int:pk>-<str:name>/', views.TaskDetailView.as_view(), name="task-detail"),
]

handler500 = views.handler500
