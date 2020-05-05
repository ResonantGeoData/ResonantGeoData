from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('algorithms/', views.algorithms, name='algorithms'),
<<<<<<< HEAD
    path('algorithms/<str:creator>/<int:pk>/', views.AlgorithmDetailView.as_view(), name='algorithm-detail'),
    path('algorithms/<str:creator>/<int:pk>/delete/', views.AlgorithmDeleteView.as_view(), name='delete-algorithm'),
    path('algorithms/new/', views.AlgorithmCreateView.as_view(), name='new-algorithm'),
=======
    path('algorithms/<str:creator>/<int:pk>/', views.AlgorithmDetailView.as_view(), name="algorithm-detail"),
    path('algorithms/<str:creator>/<int:pk>/delete/', views.AlgorithmDeleteView.as_view(), name="delete-algorithm"),
    path('algorithms/new/', views.AlgorithmCreateView.as_view(), name="new-algorithm"),
>>>>>>> Add delete algorithm view
    path('jobs/', views.jobs, name='jobs'),
<<<<<<< HEAD
    path('jobs/new/', views.JobCreateView.as_view(), name='new-job'),
    path('jobs/<str:creator>/<int:pk>/', views.JobDetailView.as_view(), name='job-detail'),
=======
    path('jobs/new/', views.JobCreateView.as_view(), name="new-job"),
    path('jobs/<str:creator>/<int:pk>/', views.JobDetailView.as_view(), name="job-detail"),
>>>>>>> Add create job view
    path('tasks/', views.tasks, name='tasks'),
<<<<<<< HEAD
    path('task/<int:pk>-<str:name>/', views.TaskDetailView.as_view(), name='task-detail'),
=======
    path('task/<int:pk>-<str:name>/', views.TaskDetailView.as_view(), name="task-detail"),
>>>>>>> Fix task detail URL
]

handler500 = views.handler500
