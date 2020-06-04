from django.shortcuts import render
from django.views import generic

from .models.dataset import Dataset

class DatasetsView(generic.ListView):
    model = Dataset
    context_object_name = 'datasets'
    queryset = Dataset.objects.all()
    template_name = 'geodata/dataset.html'
