from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('algorithms/', views.algorithms, name='algorithms'),
    path('jobs/', views.jobs, name='jobs'),
    path('tasks/', views.tasks, name='tasks'),
]

handler500 = views.handler500
