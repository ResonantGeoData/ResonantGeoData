from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
]

handler500 = views.handler500
