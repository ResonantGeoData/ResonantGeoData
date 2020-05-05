from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('algorithms/', views.algorithms, name='algorithms'),
    path('algorithms/<str:creator>/<int:pk>/', views.AlgorithmDetailView.as_view(), name="algorithm-detail"),
    path('algorithms/new/', views.AlgorithmCreateView.as_view(), name="new-algorithm"),
    path('jobs/', views.jobs, name='jobs'),
    path('tasks/', views.tasks, name='tasks'),
]

handler500 = views.handler500
